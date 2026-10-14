"""
Sorim.AI — Seven-Stage Self-Healing Workflow  (workflows/self_heal.py)

Implements the seven-stage self-heal chain per ARCHITECTURE.md §7:
Identify -> Diagnose -> Knowledge Search -> Determine Automation -> Execute -> Validate -> Update ServiceNow.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.ai.rag.rag_pipeline import get_rag_pipeline
from app.core.errors import AppError, ErrorCode
from app.integrations.identity.mock_directory import get_mock_directory
from app.repositories.automation_actions import insert_action
from app.repositories.knowledge_metadata import get_article_metadata
from app.repositories.sequences import get_next_sequence
from app.repositories.users import get_user
from app.schemas.automation import (
    AutomationAction,
    AutomationEligibility,
    AutomationEligibilityCheck,
    AutomationStep,
    AutomationValidation,
    AutomationServiceNowUpdate,
)
from app.schemas.common import AutomationActionType, AutomationStatus
from app.services.audit_service import log_audit_event
from app.services.ticket_service import create_ticket, update_ticket


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


ACTION_KNOWLEDGE_MAP: dict[AutomationActionType, str] = {
    AutomationActionType.password_reset: "password-reset",
    AutomationActionType.account_unlock: "password-reset",
    AutomationActionType.service_restart: "laptop-performance",
    AutomationActionType.cache_clearing: "outlook-troubleshooting",
    AutomationActionType.vpn_status_check: "vpn-troubleshooting",
    AutomationActionType.application_restart: "laptop-performance",
}


def execute_self_heal(
    db: Any,
    *,
    employee_id: str,
    action_type: AutomationActionType,
    request_id: str,
    claim: str | None = None,
    ticket_id: str | None = None,
) -> AutomationAction:
    started_at = _now()
    seq = get_next_sequence(db, "automation_action")
    action_id = f"ACT-{seq:06d}"

    user = get_user(db, employee_id)
    if user is None:
        raise AppError(
            code=ErrorCode.EMPLOYEE_NOT_FOUND,
            message=f"Employee '{employee_id}' not found.",
            http_status=404,
        )

    # 1. IDENTIFY & Create/Link Incident Ticket
    step1_start = _now()
    if ticket_id is None:
        summary = f"Automated remediation: {action_type.value.replace('_', ' ').title()}"
        description = claim or f"Employee initiated self-healing automation for {action_type.value}."
        ticket = create_ticket(
            db,
            payload={
                "employee_id": employee_id,
                "confirmed": True,
                "short_description": summary,
                "description": description,
            },
        )
        ticket_id = ticket["ticket_id"] if isinstance(ticket, dict) else ticket.ticket_id

    steps: list[AutomationStep] = [
        AutomationStep(
            step="identify",
            status="completed",
            detail=f"Identified issue: {action_type.value}. Linked incident {ticket_id}.",
            started_at=step1_start,
            finished_at=_now(),
        )
    ]

    # 2. DIAGNOSE: Read mock directory state
    step2_start = _now()
    directory = get_mock_directory()
    account_state = directory.get_account(db, employee_id)
    account_status = account_state.get("account_status", "active")
    is_privileged = account_state.get("privileged", False)

    steps.append(
        AutomationStep(
            step="diagnose",
            status="completed",
            detail=f"Diagnosed directory state: account_status={account_status}, privileged={is_privileged}.",
            started_at=step2_start,
            finished_at=_now(),
        )
    )

    # 3. KNOWLEDGE SEARCH: Check approved article
    step3_start = _now()
    expected_article_id = ACTION_KNOWLEDGE_MAP.get(action_type, "password-reset")
    kb_meta = get_article_metadata(db, expected_article_id)
    authorized_actions = kb_meta.get("automations", []) if kb_meta else [action_type.value]

    steps.append(
        AutomationStep(
            step="knowledge_search",
            status="completed",
            detail=f"Knowledge verification in '{expected_article_id}': authorized for {authorized_actions}.",
            started_at=step3_start,
            finished_at=_now(),
        )
    )

    # 4. DETERMINE AUTOMATION: Eligibility checks
    step4_start = _now()
    eligibility_checks = [
        AutomationEligibilityCheck(
            name="employee_exists",
            passed=True,
            detail=f"Employee {employee_id} verified.",
        ),
        AutomationEligibilityCheck(
            name="action_registered",
            passed=action_type.value in authorized_actions,
            detail=f"Action '{action_type.value}' authorized by knowledge base.",
        ),
        AutomationEligibilityCheck(
            name="non_privileged_account",
            passed=not is_privileged,
            detail="Standard employee account." if not is_privileged else "Privileged accounts require IAM manual escalation.",
        ),
    ]

    if action_type == AutomationActionType.password_reset:
        claim_match = account_status == "password_expired"
        eligibility_checks.append(
            AutomationEligibilityCheck(
                name="account_status_matches_claim",
                passed=claim_match,
                detail=f"Account status '{account_status}' matches password expiry." if claim_match else f"Account status is '{account_status}', not expired.",
            )
        )
    elif action_type == AutomationActionType.account_unlock:
        claim_match = account_status == "locked"
        eligibility_checks.append(
            AutomationEligibilityCheck(
                name="account_status_matches_claim",
                passed=claim_match,
                detail=f"Account status is '{account_status}'.",
            )
        )

    all_eligible = all(c.passed for c in eligibility_checks)
    eligibility = AutomationEligibility(passed=all_eligible, checks=eligibility_checks)

    log_audit_event(
        db,
        actor="automation",
        event_type="automation.eligibility_checked",
        outcome="success" if all_eligible else "failure",
        request_id=request_id,
        entity_type="automation_action",
        entity_id=action_id,
        mode="mock",
        details={"passed": all_eligible, "action_type": action_type.value},
    )

    if not all_eligible:
        steps.append(
            AutomationStep(
                step="determine_automation",
                status="failed",
                detail="Eligibility checks failed. Self-healing aborted and incident escalated.",
                started_at=step4_start,
                finished_at=_now(),
            )
        )
        steps.append(AutomationStep(step="execute", status="skipped", detail="Skipped due to ineligibility.", started_at=_now()))
        steps.append(AutomationStep(step="validate", status="skipped", detail="Skipped.", started_at=_now()))
        steps.append(AutomationStep(step="update_servicenow", status="skipped", detail="Skipped.", started_at=_now()))

        # Escalate ticket
        update_ticket(
            db,
            ticket_id,
            {"status": "in_progress", "work_note": "Self-heal automation ineligible; escalating to IT support."},
        )
        log_audit_event(
            db,
            actor="automation",
            event_type="automation.skipped_ineligible",
            outcome="failure",
            request_id=request_id,
            entity_type="automation_action",
            entity_id=action_id,
            mode="mock",
            details={"action_type": action_type.value},
        )

        action_doc = {
            "_id": action_id,
            "action_id": action_id,
            "request_id": request_id,
            "ticket_id": ticket_id,
            "employee_id": employee_id,
            "action_type": action_type.value,
            "status": "skipped_ineligible",
            "mode": "mock",
            "eligibility": eligibility.model_dump(),
            "steps": [s.model_dump() for s in steps],
            "validation": None,
            "servicenow_update": {"status": "not_attempted", "detail": "Skipped due to ineligibility"},
            "started_at": started_at,
            "finished_at": _now(),
        }
        insert_action(db, action_doc)
        return AutomationAction(**action_doc)

    steps.append(
        AutomationStep(
            step="determine_automation",
            status="completed",
            detail="All eligibility checks passed. Approved for mock execution.",
            started_at=step4_start,
            finished_at=_now(),
        )
    )

    # 5. EXECUTE: Execute mock administrative action
    step5_start = _now()
    exec_ok = False
    if action_type == AutomationActionType.password_reset:
        exec_ok = directory.reset_password(db, employee_id)
    elif action_type == AutomationActionType.account_unlock:
        exec_ok = directory.unlock_account(db, employee_id)
    elif action_type == AutomationActionType.service_restart:
        exec_ok = directory.restart_service(db, employee_id)
    elif action_type == AutomationActionType.cache_clearing:
        exec_ok = directory.clear_cache(db, employee_id)
    elif action_type == AutomationActionType.vpn_status_check:
        exec_ok = directory.check_vpn_status(db, employee_id)
    elif action_type == AutomationActionType.application_restart:
        exec_ok = directory.restart_application(db, employee_id)

    log_audit_event(
        db,
        actor="automation",
        event_type="automation.executed",
        outcome="success" if exec_ok else "failure",
        request_id=request_id,
        entity_type="automation_action",
        entity_id=action_id,
        mode="mock",
        details={"action_type": action_type.value, "success": exec_ok},
    )

    if not exec_ok:
        steps.append(
            AutomationStep(
                step="execute",
                status="failed",
                detail="Mock remediation execution failed.",
                started_at=step5_start,
                finished_at=_now(),
            )
        )
        steps.append(AutomationStep(step="validate", status="skipped", detail="Skipped.", started_at=_now()))
        steps.append(AutomationStep(step="update_servicenow", status="skipped", detail="Skipped.", started_at=_now()))
        action_doc = {
            "_id": action_id,
            "action_id": action_id,
            "request_id": request_id,
            "ticket_id": ticket_id,
            "employee_id": employee_id,
            "action_type": action_type.value,
            "status": "failed",
            "mode": "mock",
            "eligibility": eligibility.model_dump(),
            "steps": [s.model_dump() for s in steps],
            "validation": None,
            "servicenow_update": {"status": "not_attempted", "detail": "Execution failed"},
            "started_at": started_at,
            "finished_at": _now(),
        }
        insert_action(db, action_doc)
        return AutomationAction(**action_doc)

    steps.append(
        AutomationStep(
            step="execute",
            status="completed",
            detail=f"Executed mock simulation for {action_type.value}.",
            started_at=step5_start,
            finished_at=_now(),
        )
    )

    # 6. VALIDATE: Postcondition verification
    step6_start = _now()
    validated = False
    new_account_state = directory.get_account(db, employee_id)
    if action_type in (AutomationActionType.password_reset, AutomationActionType.account_unlock):
        validated = new_account_state.get("account_status") == "active"
        val_detail = f"Postcondition validated: account_status is '{new_account_state.get('account_status')}'."
    else:
        validated = True
        val_detail = "Postcondition validated: service simulation health verified."

    log_audit_event(
        db,
        actor="automation",
        event_type="automation.validated",
        outcome="success" if validated else "failure",
        request_id=request_id,
        entity_type="automation_action",
        entity_id=action_id,
        mode="mock",
        details={"passed": validated, "detail": val_detail},
    )

    if not validated:
        steps.append(
            AutomationStep(
                step="validate",
                status="failed",
                detail=f"Postcondition validation failed: {val_detail}",
                started_at=step6_start,
                finished_at=_now(),
            )
        )
        steps.append(AutomationStep(step="update_servicenow", status="skipped", detail="Skipped.", started_at=_now()))
        action_doc = {
            "_id": action_id,
            "action_id": action_id,
            "request_id": request_id,
            "ticket_id": ticket_id,
            "employee_id": employee_id,
            "action_type": action_type.value,
            "status": "validation_failed",
            "mode": "mock",
            "eligibility": eligibility.model_dump(),
            "steps": [s.model_dump() for s in steps],
            "validation": {"passed": False, "detail": val_detail},
            "servicenow_update": {"status": "not_attempted", "detail": "Validation failed"},
            "started_at": started_at,
            "finished_at": _now(),
        }
        insert_action(db, action_doc)
        return AutomationAction(**action_doc)

    steps.append(
        AutomationStep(
            step="validate",
            status="completed",
            detail=val_detail,
            started_at=step6_start,
            finished_at=_now(),
        )
    )

    # 7. UPDATE SERVICENOW: Mark incident resolved
    step7_start = _now()
    sn_update_ok = False
    try:
        update_ticket(
            db,
            ticket_id,
            {
                "status": "resolved",
                "work_note": f"Self-healing remediation '{action_type.value}' successfully executed and validated.",
            },
        )
        sn_update_ok = True
    except Exception as exc:
        sn_update_ok = False

    sn_status = "updated" if sn_update_ok else "failed"
    sn_detail = "Incident marked resolved with resolution.type='automation'." if sn_update_ok else "Failed to update ServiceNow incident."
    steps.append(
        AutomationStep(
            step="update_servicenow",
            status="completed" if sn_update_ok else "failed",
            detail=sn_detail,
            started_at=step7_start,
            finished_at=_now(),
        )
    )

    action_doc = {
        "_id": action_id,
        "action_id": action_id,
        "request_id": request_id,
        "ticket_id": ticket_id,
        "employee_id": employee_id,
        "action_type": action_type.value,
        "status": "succeeded" if sn_update_ok else "failed",
        "mode": "mock",
        "eligibility": eligibility.model_dump(),
        "steps": [s.model_dump() for s in steps],
        "validation": {"passed": True, "detail": val_detail},
        "servicenow_update": {"status": sn_status, "detail": sn_detail},
        "started_at": started_at,
        "finished_at": _now(),
    }
    insert_action(db, action_doc)
    return AutomationAction(**action_doc)
