"""
Sorim.AI — Central Request Router  (workflows/request_router.py)

Orchestrates POST /api/v1/chat:
Analysis -> Intent Routing (Knowledge / Incident / Automatable / Software) -> ChatRecord.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

from app.ai.analysis.request_analyzer import analyze_request
from app.ai.rag.rag_pipeline import get_rag_pipeline
from app.ai.safety.confidence import compute_confidence
from app.ai.safety.escalation import determine_escalation
from app.core.config import get_settings
from app.core.errors import AppError, ErrorCode
from app.repositories.automation_actions import get_action
from app.repositories.chat_history import get_chat_record, insert_chat_record
from app.repositories.sequences import get_next_sequence
from app.repositories.software_requests import get_request as get_sw_request
from app.repositories.tickets import get_ticket
from app.repositories.users import get_user
from app.schemas.analysis import Analysis, ChatRecord, Confidence, Escalation, Timings
from app.schemas.common import EscalationReason, Intent, Outcome
from app.services.audit_service import log_audit_event
from app.workflows.provisioning import handle_software_request
from app.workflows.self_heal import execute_self_heal


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def route_chat_request(
    db: Any,
    *,
    employee_id: str,
    message: str,
    conversation_id: str | None = None,
) -> ChatRecord:
    start_time = time.monotonic()
    user = get_user(db, employee_id)
    if user is None:
        raise AppError(
            code=ErrorCode.EMPLOYEE_NOT_FOUND,
            message=f"Employee '{employee_id}' was not found.",
            http_status=404,
        )

    seq = get_next_sequence(db, "ai_request")
    request_id = f"AIR-{seq:06d}"

    if conversation_id is None:
        cnv_seq = get_next_sequence(db, "conversation")
        conversation_id = f"CNV-{cnv_seq:06d}"

    # 1. AI Analysis
    analysis_start = time.monotonic()
    analysis_res: Analysis | None = None
    analysis_failed = False
    try:
        analysis_tuple = analyze_request(message)
        analysis_res = analysis_tuple[0]
    except AppError as exc:
        if exc.code == ErrorCode.LLM_OUTPUT_INVALID:
            analysis_failed = True
        else:
            analysis_failed = True
    except Exception:
        analysis_failed = True
    analysis_ms = int((time.monotonic() - analysis_start) * 1000)

    rag = get_rag_pipeline()
    created_at = _now()
    llm_id = get_settings().llm_model_id

    # If analysis failed or model unclassifiable:
    if analysis_failed or analysis_res is None:
        total_ms = int((time.monotonic() - start_time) * 1000)
        chat_doc = {
            "_id": request_id,
            "request_id": request_id,
            "entry_type": "chat",
            "conversation_id": conversation_id,
            "employee_id": employee_id,
            "message": message,
            "analysis": None,
            "answer": "I was unable to analyze your request automatically. You can review and submit an incident ticket manually.",
            "sources": [],
            "confidence": None,
            "outcome": Outcome.analysis_failed.value,
            "escalation": {
                "required": True,
                "reason": EscalationReason.analysis_failed.value,
                "message": "AI analysis was unable to classify this request.",
                "ticket_option_available": True,
            },
            "ticket_id": None,
            "automation_action_id": None,
            "software_request_id": None,
            "timings_ms": {"analysis": analysis_ms, "retrieval": None, "generation": None, "total": total_ms},
            "llm_model_id": llm_id,
            "created_at": created_at,
        }
        insert_chat_record(db, chat_doc)
        return ChatRecord(**chat_doc)

    # ROUTE BY INTENT
    intent = analysis_res.intent

    # Intent 1: Knowledge Question
    if intent == Intent.knowledge_question:
        rag_resp = rag.search_and_answer(message, mode="answer")
        outcome = (
            Outcome.insufficient_knowledge.value
            if rag_resp.insufficient_knowledge
            else Outcome.answered.value
        )
        total_ms = int((time.monotonic() - start_time) * 1000)
        sources_list = [s.model_dump() for s in rag_resp.hits]
        chat_doc = {
            "_id": request_id,
            "request_id": request_id,
            "entry_type": "chat",
            "conversation_id": conversation_id,
            "employee_id": employee_id,
            "message": message,
            "analysis": analysis_res.model_dump(),
            "answer": rag_resp.answer,
            "sources": sources_list,
            "confidence": rag_resp.confidence.model_dump() if rag_resp.confidence else None,
            "outcome": outcome,
            "escalation": rag_resp.escalation.model_dump(),
            "ticket_id": None,
            "automation_action_id": None,
            "software_request_id": None,
            "timings_ms": {
                "analysis": analysis_ms,
                "retrieval": rag_resp.timings_ms.retrieval,
                "generation": rag_resp.timings_ms.generation,
                "total": total_ms,
            },
            "llm_model_id": llm_id,
            "created_at": created_at,
        }
        insert_chat_record(db, chat_doc)
        return ChatRecord(**chat_doc)

    # Intent 2: Incident
    elif intent == Intent.incident:
        rag_resp = rag.search_and_answer(message, mode="retrieve")
        total_ms = int((time.monotonic() - start_time) * 1000)
        sources_list = [s.model_dump() for s in rag_resp.hits]
        suggested_step = (
            f"Suggested resolution: {analysis_res.suggested_resolution}. "
            "Please review the proposed ticket classification below and confirm to submit."
        )
        conf = compute_confidence(classification_agreement=1.0, retrieval_top_score=rag_resp.hits[0].score if rag_resp.hits else 0.5)
        chat_doc = {
            "_id": request_id,
            "request_id": request_id,
            "entry_type": "chat",
            "conversation_id": conversation_id,
            "employee_id": employee_id,
            "message": message,
            "analysis": analysis_res.model_dump(),
            "answer": suggested_step,
            "sources": sources_list,
            "confidence": conf.model_dump(),
            "outcome": Outcome.ticket_suggested.value,
            "escalation": {
                "required": False,
                "reason": None,
                "message": None,
                "ticket_option_available": True,
            },
            "ticket_id": None,
            "automation_action_id": None,
            "software_request_id": None,
            "timings_ms": {
                "analysis": analysis_ms,
                "retrieval": rag_resp.timings_ms.retrieval,
                "generation": None,
                "total": total_ms,
            },
            "llm_model_id": llm_id,
            "created_at": created_at,
        }
        insert_chat_record(db, chat_doc)
        return ChatRecord(**chat_doc)

    # Intent 3: Automatable Issue
    elif intent == Intent.automatable_issue:
        action_type = analysis_res.automation_action_type
        if action_type is None:
            from app.schemas.common import AutomationActionType
            action_type = AutomationActionType.password_reset

        auto_action = execute_self_heal(
            db,
            employee_id=employee_id,
            action_type=action_type,
            request_id=request_id,
            claim=message,
        )
        total_ms = int((time.monotonic() - start_time) * 1000)
        is_resolved = auto_action.status.value == "succeeded"
        outcome = Outcome.automation_resolved.value if is_resolved else Outcome.automation_escalated.value
        answer = (
            f"Self-healing automation for '{action_type.value}' executed successfully and verified. Ticket marked resolved."
            if is_resolved
            else f"Self-healing automation for '{action_type.value}' was ineligible or could not complete. Ticket escalated to support."
        )
        conf = compute_confidence(classification_agreement=1.0, retrieval_top_score=0.9, grounding_score=1.0)
        chat_doc = {
            "_id": request_id,
            "request_id": request_id,
            "entry_type": "chat",
            "conversation_id": conversation_id,
            "employee_id": employee_id,
            "message": message,
            "analysis": analysis_res.model_dump(),
            "answer": answer,
            "sources": [],
            "confidence": conf.model_dump(),
            "outcome": outcome,
            "escalation": {
                "required": not is_resolved,
                "reason": EscalationReason.automation_failed.value if not is_resolved else None,
                "message": "Automation escalated." if not is_resolved else None,
                "ticket_option_available": True,
            },
            "ticket_id": auto_action.ticket_id,
            "automation_action_id": auto_action.action_id,
            "software_request_id": None,
            "timings_ms": {"analysis": analysis_ms, "retrieval": None, "generation": None, "total": total_ms},
            "llm_model_id": llm_id,
            "created_at": created_at,
        }
        insert_chat_record(db, chat_doc)
        res = ChatRecord(**chat_doc)
        res.automation = auto_action.model_dump()
        return res

    # Intent 4: Service Request (Software)
    elif intent == Intent.service_request:
        sw_name = analysis_res.software_name or message
        total_ms = int((time.monotonic() - start_time) * 1000)
        try:
            sw_req = handle_software_request(
                db,
                employee_id=employee_id,
                software_name=sw_name,
                request_id=request_id,
            )
            answer = f"Your request for {sw_req.software.name} has been submitted (Request ID: {sw_req.servicenow_ref.number}) and is provisioned (simulated)."
            chat_doc = {
                "_id": request_id,
                "request_id": request_id,
                "entry_type": "chat",
                "conversation_id": conversation_id,
                "employee_id": employee_id,
                "message": message,
                "analysis": analysis_res.model_dump(),
                "answer": answer,
                "sources": [],
                "confidence": compute_confidence(classification_agreement=1.0).model_dump(),
                "outcome": Outcome.software_request_created.value,
                "escalation": {
                    "required": False,
                    "reason": None,
                    "message": None,
                    "ticket_option_available": True,
                },
                "ticket_id": None,
                "automation_action_id": None,
                "software_request_id": sw_req.software_request_id,
                "timings_ms": {"analysis": analysis_ms, "retrieval": None, "generation": None, "total": total_ms},
                "llm_model_id": llm_id,
                "created_at": created_at,
            }
            insert_chat_record(db, chat_doc)
            rec = ChatRecord(**chat_doc)
            rec.software_request = sw_req.model_dump()
            return rec
        except AppError as exc:
            answer = f"The requested software '{sw_name}' is not in the approved corporate catalogue."
            chat_doc = {
                "_id": request_id,
                "request_id": request_id,
                "entry_type": "chat",
                "conversation_id": conversation_id,
                "employee_id": employee_id,
                "message": message,
                "analysis": analysis_res.model_dump(),
                "answer": answer,
                "sources": [],
                "confidence": compute_confidence(classification_agreement=0.5).model_dump(),
                "outcome": Outcome.software_not_available.value,
                "escalation": {
                    "required": True,
                    "reason": EscalationReason.software_not_available.value,
                    "message": "Software is not in catalogue.",
                    "ticket_option_available": True,
                },
                "ticket_id": None,
                "automation_action_id": None,
                "software_request_id": None,
                "timings_ms": {"analysis": analysis_ms, "retrieval": None, "generation": None, "total": total_ms},
                "llm_model_id": llm_id,
                "created_at": created_at,
            }
            insert_chat_record(db, chat_doc)
            return ChatRecord(**chat_doc)

    # Fallback
    total_ms = int((time.monotonic() - start_time) * 1000)
    chat_doc = {
        "_id": request_id,
        "request_id": request_id,
        "entry_type": "chat",
        "conversation_id": conversation_id,
        "employee_id": employee_id,
        "message": message,
        "analysis": analysis_res.model_dump(),
        "answer": "Request processed.",
        "sources": [],
        "confidence": None,
        "outcome": Outcome.analysis_only.value,
        "escalation": {"required": False, "reason": None, "message": None, "ticket_option_available": True},
        "ticket_id": None,
        "automation_action_id": None,
        "software_request_id": None,
        "timings_ms": {"analysis": analysis_ms, "retrieval": None, "generation": None, "total": total_ms},
        "llm_model_id": llm_id,
        "created_at": created_at,
    }
    insert_chat_record(db, chat_doc)
    return ChatRecord(**chat_doc)


def hydrate_chat_record(db: Any, record: dict[str, Any]) -> ChatRecord:
    rec = ChatRecord(**record)
    if record.get("ticket_id"):
        ticket_doc = get_ticket(db, record["ticket_id"])
        if ticket_doc:
            rec.ticket = ticket_doc
    if record.get("automation_action_id"):
        action_doc = get_action(db, record["automation_action_id"])
        if action_doc:
            rec.automation = action_doc
    if record.get("software_request_id"):
        sw_doc = get_sw_request(db, record["software_request_id"])
        if sw_doc:
            rec.software_request = sw_doc
    return rec
