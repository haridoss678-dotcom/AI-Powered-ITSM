"""
Sorim.AI — Automation Action Routes  (api/routes/automation.py)

Implements E-13 and direct self-healing trigger.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_db
from app.repositories.automation_actions import list_actions
from app.repositories.sequences import get_next_sequence
from app.schemas.automation import AutomationAction, AutomationExecuteRequest
from app.schemas.common import Page
from app.workflows.self_heal import execute_self_heal

router = APIRouter(prefix="/automation", tags=["automation"])


@router.get(
    "/actions",
    response_model=Page[AutomationAction],
    summary="List automation action history",
)
def get_automation_actions(
    status: str | None = Query(default=None),
    employee_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    skip: int = Query(default=0, ge=0),
    db: Any = Depends(get_db),
) -> Page[AutomationAction]:
    items, total = list_actions(db, status=status, employee_id=employee_id, skip=skip, limit=limit)
    return Page(
        items=[AutomationAction(**it) for it in items],
        total=total,
        limit=limit,
        skip=skip,
    )


@router.post(
    "/execute",
    response_model=AutomationAction,
    summary="Trigger the seven-stage self-healing remediation workflow",
)
def trigger_self_heal(
    payload: AutomationExecuteRequest,
    db: Any = Depends(get_db),
) -> AutomationAction:
    seq = get_next_sequence(db, "ai_request")
    request_id = f"AIR-{seq:06d}"
    return execute_self_heal(
        db,
        employee_id=payload.employee_id,
        action_type=payload.action_type,
        request_id=request_id,
        claim=payload.claim,
    )
