"""
Sorim.AI — Chat Routes  (api/routes/chat.py)

Implements E-10, E-11, E-12 per API_CONTRACTS.md §6.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_db
from app.core.errors import AppError, ErrorCode
from app.repositories.chat_history import get_chat_record, list_chat_records
from app.schemas.analysis import ChatRecord
from app.schemas.chat import ChatRequest
from app.schemas.common import Page
from app.workflows.request_router import hydrate_chat_record, route_chat_request

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post(
    "",
    response_model=ChatRecord,
    summary="Submit an employee chat message and execute intent workflow",
)
def handle_chat_message(
    payload: ChatRequest,
    db: Any = Depends(get_db),
) -> ChatRecord:
    return route_chat_request(
        db,
        employee_id=payload.employee_id,
        message=payload.message,
        conversation_id=payload.conversation_id,
    )


@router.get(
    "/requests",
    response_model=Page[ChatRecord],
    summary="List past AI request and chat history records",
)
def list_chat_history(
    employee_id: str | None = Query(default=None),
    entry_type: str | None = Query(default=None),
    conversation_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    skip: int = Query(default=0, ge=0),
    db: Any = Depends(get_db),
) -> Page[ChatRecord]:
    items, total = list_chat_records(
        db,
        employee_id=employee_id,
        entry_type=entry_type,
        conversation_id=conversation_id,
        skip=skip,
        limit=limit,
    )
    hydrated = [hydrate_chat_record(db, it) for it in items]
    return Page(items=hydrated, total=total, limit=limit, skip=skip)


@router.get(
    "/requests/{request_id}",
    response_model=ChatRecord,
    summary="Get single AI request details with full metadata and hydrated links",
)
def get_chat_history_detail(
    request_id: str,
    db: Any = Depends(get_db),
) -> ChatRecord:
    record = get_chat_record(db, request_id)
    if record is None:
        raise AppError(
            code=ErrorCode.NOT_FOUND,
            message=f"AI request '{request_id}' was not found.",
            http_status=404,
        )
    return hydrate_chat_record(db, record)
