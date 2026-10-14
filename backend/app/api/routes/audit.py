"""
Sorim.AI — Audit Log Routes  (api/routes/audit.py)

Implements E-14: GET /api/v1/audit-logs per API_CONTRACTS.md §7.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_db
from app.repositories.audit_logs import query_events
from app.schemas.audit import AuditLog
from app.schemas.common import Page

router = APIRouter(tags=["audit"])


@router.get(
    "/audit-logs",
    response_model=Page[AuditLog],
    summary="Query audit log entries",
)
def get_audit_logs(
    request_id: str | None = Query(default=None),
    entity_type: str | None = Query(default=None),
    entity_id: str | None = Query(default=None),
    event_type: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    skip: int = Query(default=0, ge=0),
    db: Any = Depends(get_db),
) -> Page[AuditLog]:
    items, total = query_events(
        db,
        request_id=request_id,
        entity_type=entity_type,
        entity_id=entity_id,
        event_type=event_type,
        skip=skip,
        limit=limit,
    )
    return Page(
        items=[
            AuditLog(
                audit_id=it.get("_id", it.get("audit_id", "")),
                timestamp=it.get("timestamp", ""),
                actor=it.get("actor", "system"),
                event_type=it.get("event_type", ""),
                outcome=it.get("outcome", "success"),
                request_id=it.get("request_id"),
                entity_type=it.get("entity_type"),
                entity_id=it.get("entity_id"),
                mode=it.get("mode"),
                details=it.get("details", {}),
            )
            for it in items
        ],
        total=total,
        limit=limit,
        skip=skip,
    )
