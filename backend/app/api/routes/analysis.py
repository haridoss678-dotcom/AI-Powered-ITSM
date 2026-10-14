from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, status

from app.ai.analysis.request_analyzer import analyze_request
from app.api.deps import get_db
from app.core.config import get_settings
from app.core.errors import AppError, ErrorCode
from app.repositories.chat_history import insert_chat_record
from app.repositories.sequences import get_next_sequence
from app.repositories.users import get_user
from app.schemas.analysis import AnalysisRequest, ChatRecord, Escalation, Timings
from app.schemas.common import EscalationReason, Outcome
from app.services.audit_service import log_audit_event

router = APIRouter(prefix="/tickets", tags=["analysis"])


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _failure_record(
    db: Any,
    *,
    request_id: str,
    payload: AnalysisRequest,
    started: float,
) -> dict[str, Any]:
    settings = get_settings()
    now = _now_iso()
    total_ms = int((time.monotonic() - started) * 1000)
    record = {
        "_id": request_id,
        "request_id": request_id,
        "entry_type": "analysis",
        "conversation_id": None,
        "employee_id": payload.employee_id,
        "message": payload.message,
        "analysis": None,
        "answer": None,
        "sources": [],
        "confidence": None,
        "outcome": Outcome.analysis_failed.value,
        "escalation": {
            "required": True,
            "reason": EscalationReason.analysis_failed.value,
            "message": "AI could not analyse this request. You can create a ticket manually.",
            "ticket_option_available": True,
        },
        "ticket_id": None,
        "automation_action_id": None,
        "software_request_id": None,
        "timings_ms": {
            "analysis": total_ms,
            "retrieval": None,
            "generation": None,
            "total": total_ms,
        },
        "llm_model_id": settings.llm_model_id,
        "created_at": now,
    }
    insert_chat_record(db, record)
    log_audit_event(
        db,
        actor="ai",
        event_type="ai.analysis_failed",
        outcome="failure",
        entity_type="ai_request",
        entity_id=request_id,
        request_id=request_id,
        details={"reason": "invalid_model_output"},
        mode=None,
    )
    return record


@router.post(
    "/analyze",
    response_model=ChatRecord,
    responses={502: {"description": "Model output did not validate after one retry."}},
)
def analyze_ticket_route(
    payload: AnalysisRequest,
    db=Depends(get_db),
):
    if get_user(db, payload.employee_id) is None:
        raise AppError(
            code=ErrorCode.EMPLOYEE_NOT_FOUND,
            message=f"Employee '{payload.employee_id}' was not found.",
            http_status=status.HTTP_404_NOT_FOUND,
        )

    request_id = f"AIR-{get_next_sequence(db, 'ai_request'):06d}"
    started = time.monotonic()
    try:
        analysis, confidence, attempts = analyze_request(payload.message)
    except AppError as exc:
        if exc.code == ErrorCode.MODEL_UNAVAILABLE:
            log_audit_event(
                db,
                actor="ai",
                event_type="ai.model_error",
                outcome="failure",
                entity_type="ai_request",
                entity_id=request_id,
                request_id=request_id,
                details={"code": exc.code},
                mode=None,
            )
        raise
    except ValueError as exc:
        _failure_record(db, request_id=request_id, payload=payload, started=started)
        raise AppError(
            code=ErrorCode.LLM_OUTPUT_INVALID,
            message="The model output could not be validated. You can create a ticket manually.",
            http_status=status.HTTP_502_BAD_GATEWAY,
            details={"request_id": request_id},
        ) from exc

    now = _now_iso()
    analysis_ms = int((time.monotonic() - started) * 1000)
    low_confidence = confidence["below_threshold"]
    escalation = Escalation(
        required=low_confidence,
        reason=EscalationReason.low_confidence if low_confidence else None,
        message="Analysis confidence is below the configured threshold." if low_confidence else None,
        ticket_option_available=True,
    )
    record = {
        "_id": request_id,
        "request_id": request_id,
        "entry_type": "analysis",
        "conversation_id": None,
        "employee_id": payload.employee_id,
        "message": payload.message,
        "analysis": analysis.model_dump(mode="json"),
        "answer": None,
        "sources": [],
        "confidence": confidence,
        "outcome": Outcome.analysis_only.value,
        "escalation": escalation.model_dump(mode="json"),
        "ticket_id": None,
        "automation_action_id": None,
        "software_request_id": None,
        "timings_ms": Timings(
            analysis=analysis_ms,
            retrieval=None,
            generation=None,
            total=analysis_ms,
        ).model_dump(),
        "llm_model_id": analysis.model_id,
        "created_at": now,
    }
    insert_chat_record(db, record)
    log_audit_event(
        db,
        actor="ai",
        event_type="ai.analysis_completed",
        outcome="success",
        entity_type="ai_request",
        entity_id=request_id,
        request_id=request_id,
        details={"intent": analysis.intent.value, "llm_attempts": attempts},
        mode=None,
    )
    return ChatRecord.model_validate(
        {
            key: value
            for key, value in record.items()
            if key not in {"_id", "ticket_id", "automation_action_id", "software_request_id"}
        }
    )
