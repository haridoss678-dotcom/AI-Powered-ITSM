from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pymongo.errors import PyMongoError

from app.ai.analysis.taxonomy import assignment_group
from app.core.errors import AppError, ErrorCode
from app.integrations.servicenow.factory import get_servicenow_client
from app.repositories.chat_history import get_chat_record, link_ticket_to_chat_record
from app.repositories.sequences import get_next_sequence
from app.repositories.tickets import find_by_request_id, get_ticket, insert_ticket, list_tickets, update_ticket
from app.repositories.users import get_user
from app.services.audit_service import log_audit_event


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _serialize_ticket(doc: dict[str, Any]) -> dict[str, Any]:
    clean = {k: v for k, v in doc.items() if k not in ("_id", "work_note")}
    return clean


def create_ticket(db: Any, payload: dict[str, Any]) -> dict[str, Any]:
    employee_id = payload.get("employee_id")
    try:
        employee = get_user(db, employee_id or "")
    except PyMongoError as exc:
        raise AppError(
            code=ErrorCode.DATABASE_UNAVAILABLE,
            message="Ticket creation could not read the requester from the database.",
            http_status=503,
        ) from exc
    if not employee:
        raise AppError(
            code=ErrorCode.EMPLOYEE_NOT_FOUND,
            message=f"Employee '{employee_id}' was not found.",
            http_status=404,
        )

    if not payload.get("confirmed"):
        raise AppError(
            code=ErrorCode.VALIDATION_ERROR,
            message="Employee confirmation is required before creating a ticket.",
            http_status=422,
        )

    request_id = payload.get("request_id")
    client = get_servicenow_client()

    def create_in_transaction(session: Any) -> dict[str, Any]:
        analysis_record = None
        if request_id:
            existing = find_by_request_id(db, request_id, session=session)
            if existing is not None:
                raise AppError(
                    code=ErrorCode.CONFLICT,
                    message=f"Ticket for request '{request_id}' already exists.",
                    http_status=409,
                    details={"ticket_id": existing.get("ticket_id", existing.get("_id"))},
                )
            analysis_record = get_chat_record(db, request_id, session=session)
            if analysis_record is None:
                raise AppError(
                    code=ErrorCode.NOT_FOUND,
                    message=f"Analysis request '{request_id}' was not found.",
                    http_status=404,
                )
            if analysis_record.get("employee_id") != employee_id:
                raise AppError(
                    code=ErrorCode.VALIDATION_ERROR,
                    message="The analysis request does not belong to the selected employee.",
                    http_status=422,
                )
            if analysis_record.get("ticket_id"):
                raise AppError(
                    code=ErrorCode.DATABASE_UNAVAILABLE,
                    message="The analysis request is linked to a ticket that cannot be found.",
                    http_status=503,
                )
            analysis = (analysis_record.get("analysis") or {})
            intent = analysis.get("intent")
            category = analysis.get("category")
            subcategory = analysis.get("subcategory")
            escalation_required = bool(
                (analysis_record.get("escalation") or {}).get("required")
            )
            # If the category is a break-fix incident (Network, Hardware, Email) or VPN/Wi-Fi/Outlook, it is eligible for incident creation
            is_break_fix = (
                category in {"Network", "Hardware", "Email & Collaboration"}
                or subcategory in {"VPN", "Wi-Fi", "Outlook", "Laptop Performance"}
            )
            if (intent == "service_request") or (
                intent == "knowledge_question" and not escalation_required
            ) or (
                intent == "automatable_issue" and not is_break_fix and not escalation_required and not payload.get("confirmed")
            ):
                raise AppError(
                    code=ErrorCode.VALIDATION_ERROR,
                    message="This analysis is not eligible for incident creation.",
                    http_status=422,
                )

        seq = get_next_sequence(db, "ticket", session=session)
        ticket_id = f"TKT-{seq:06d}"
        created_at = _now_iso()
        analysis = (analysis_record or {}).get("analysis") or {}
        short_description = (
            payload.get("short_description") or analysis.get("summary") or "Support request"
        ).strip()
        description = (
            payload.get("description")
            or (analysis_record or {}).get("message")
            or short_description
        ).strip()
        category = analysis.get("category") or "Other"
        subcategory = analysis.get("subcategory") or "Uncategorized"
        priority = analysis.get("priority") or "P3"
        impact = analysis.get("impact") or "individual"
        urgency = analysis.get("urgency") or "medium"
        group = analysis.get("assignment_group")
        if not group:
            try:
                group = assignment_group(category, subcategory)
            except ValueError:
                group = "Service Desk"
        escalation = (analysis_record or {}).get("escalation") or {}
        escalated = bool(escalation.get("required"))
        escalation_reason = escalation.get("reason") if escalated else None

        servicenow_ref = client.create_incident(
            db,
            {
                "ticket_id": ticket_id,
                "employee_id": employee_id,
                "short_description": short_description,
                "description": description,
                "category": category,
                "subcategory": subcategory,
                "priority": priority,
                "assignment_group": group,
                "impact": impact,
                "urgency": urgency,
                "number": f"INC{seq:06d}",
                "created_at": created_at,
            },
            session=session,
        )
        doc = {
            "_id": ticket_id,
            "ticket_id": ticket_id,
            "status": "open",
            "source": "chat_analysis" if request_id else "manual",
            "requester": {"employee_id": employee_id, "name": employee.get("name")},
            "short_description": short_description,
            "description": description,
            "intent": "incident",
            "category": category,
            "subcategory": subcategory,
            "priority": priority,
            "impact": impact,
            "urgency": urgency,
            "assignment_group": group,
            "suggested_resolution": analysis.get("suggested_resolution"),
            "escalated": escalated,
            "escalation_reason": escalation_reason,
            "resolution": None,
            "servicenow_ref": servicenow_ref,
            "automation_action_id": None,
            "work_notes": [
                {"timestamp": created_at, "actor": "employee", "text": "Ticket created."}
            ],
            "created_at": created_at,
            "updated_at": created_at,
        }
        if request_id is not None:
            doc["request_id"] = request_id
        insert_ticket(db, doc, session=session)
        if request_id and not link_ticket_to_chat_record(
            db, request_id, ticket_id=ticket_id, session=session
        ):
            existing = find_by_request_id(db, request_id, session=session)
            if existing is not None:
                raise AppError(
                    code=ErrorCode.CONFLICT,
                    message=f"Ticket for request '{request_id}' already exists.",
                    http_status=409,
                    details={"ticket_id": existing.get("ticket_id", existing.get("_id"))},
                )
            raise AppError(
                code=ErrorCode.DATABASE_UNAVAILABLE,
                message="The analysis request could not be linked to its ticket.",
                http_status=503,
            )
        log_audit_event(
            db,
            actor="employee",
            event_type="ticket.created",
            outcome="success",
            entity_type="ticket",
            entity_id=ticket_id,
            request_id=request_id,
            details={"employee_id": employee_id, "servicenow_number": servicenow_ref["number"]},
            session=session,
        )
        log_audit_event(
            db,
            actor="system",
            event_type="servicenow.incident_created",
            outcome="success",
            entity_type="servicenow",
            entity_id=servicenow_ref["sys_id"],
            request_id=request_id,
            details={"ticket_id": ticket_id, "number": servicenow_ref["number"], "mode": "mock"},
            session=session,
        )
        return _serialize_ticket(doc)

    try:
        with db.client.start_session() as session:
            return session.with_transaction(create_in_transaction)
    except AppError as exc:
        if exc.code == ErrorCode.SERVICENOW_UNAVAILABLE:
            try:
                log_audit_event(
                    db,
                    actor="system",
                    event_type="servicenow.failed",
                    outcome="failure",
                    entity_type="servicenow",
                    request_id=request_id,
                    details={"operation": "incident_create", "code": exc.code, "mode": "mock"},
                )
            except PyMongoError as audit_error:
                raise AppError(
                    code=ErrorCode.DATABASE_UNAVAILABLE,
                    message="The ServiceNow failure could not be recorded because the database is unavailable.",
                    http_status=503,
                ) from audit_error
        raise
    except PyMongoError as exc:
        raise AppError(
            code=ErrorCode.DATABASE_UNAVAILABLE,
            message="Ticket creation could not be committed to the database.",
            http_status=503,
        ) from exc


def get_ticket_by_id(db: Any, ticket_id: str) -> dict[str, Any]:
    ticket = get_ticket(db, ticket_id)
    if ticket is None:
        raise AppError(
            code=ErrorCode.NOT_FOUND,
            message=f"Ticket '{ticket_id}' was not found.",
            http_status=404,
        )
    return _serialize_ticket(ticket)


def list_ticket_records(db: Any, *, status: str | None = None, escalated: bool | None = None, employee_id: str | None = None, skip: int = 0, limit: int = 50) -> dict[str, Any]:
    if employee_id is not None and get_user(db, employee_id) is None:
        raise AppError(
            code=ErrorCode.EMPLOYEE_NOT_FOUND,
            message=f"Employee '{employee_id}' was not found.",
            http_status=404,
        )

    items, total = list_tickets(
        db,
        status=status,
        escalated=escalated,
        employee_id=employee_id,
        skip=skip,
        limit=limit,
    )
    return {"items": [_serialize_ticket(item) for item in items], "total": total, "limit": limit, "skip": skip}


def update_ticket_record(db: Any, ticket_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    ticket = get_ticket_by_id(db, ticket_id)
    status = payload.get("status")
    work_note = payload.get("work_note")

    if status is not None and status not in {"open", "in_progress", "resolved", "closed"}:
        raise AppError(
            code=ErrorCode.INVALID_TRANSITION,
            message=f"Unsupported ticket status '{status}'.",
            http_status=409,
        )

    allowed = {
        "open": {"in_progress", "resolved"},
        "in_progress": {"resolved"},
        "resolved": {"closed", "in_progress"},
        "closed": set(),
    }
    current = ticket["status"]
    if status is not None and status == current:
        raise AppError(
            code=ErrorCode.INVALID_TRANSITION,
            message=f"Ticket '{ticket_id}' is already in status '{current}'.",
            http_status=409,
        )
    if status is not None and status not in allowed.get(current, set()):
        raise AppError(
            code=ErrorCode.INVALID_TRANSITION,
            message=f"Cannot transition ticket '{ticket_id}' from '{current}' to '{status}'.",
            http_status=409,
        )

    patch: dict[str, Any] = {"updated_at": _now_iso()}
    if status is not None:
        patch["status"] = status
        if status == "resolved":
            patch["resolution"] = {
                "type": "human",
                "resolved_at": patch["updated_at"],
                "notes": work_note,
            }
        elif current == "resolved" and status == "in_progress":
            patch["resolution"] = None
    if work_note:
        existing = ticket.get("work_notes", [])
        existing.append({"timestamp": patch["updated_at"], "actor": "system", "text": work_note})
        patch["work_notes"] = existing

    client = get_servicenow_client()
    updated_at = patch["updated_at"]
    try:
        client.update_incident(
            db,
            ticket["servicenow_ref"]["sys_id"],
            {
                "status": status or current,
                "work_note": work_note,
                "updated_at": updated_at,
            },
        )
    except AppError as exc:
        log_audit_event(
            db,
            actor="system",
            event_type="servicenow.failed",
            outcome="failure",
            entity_type="servicenow",
            entity_id=ticket["servicenow_ref"]["sys_id"],
            request_id=ticket.get("request_id"),
            details={"operation": "incident_update", "code": exc.code, "mode": "mock"},
        )
        raise

    updated = update_ticket(db, ticket_id, patch)
    if updated is None:
        raise AppError(
            code=ErrorCode.NOT_FOUND,
            message=f"Ticket '{ticket_id}' was not found.",
            http_status=404,
        )
    log_audit_event(
        db,
        actor="system",
        event_type="ticket.updated",
        outcome="success",
        entity_type="ticket",
        entity_id=ticket_id,
        details={"status": status, "work_note": bool(work_note)},
    )
    log_audit_event(
        db,
        actor="system",
        event_type="servicenow.incident_updated",
        outcome="success",
        entity_type="servicenow",
        entity_id=ticket["servicenow_ref"]["sys_id"],
        request_id=ticket.get("request_id"),
        details={"ticket_id": ticket_id, "status": status or current, "mode": "mock"},
    )
    return _serialize_ticket(updated)
