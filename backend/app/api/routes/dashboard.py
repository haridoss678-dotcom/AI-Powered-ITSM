"""
Sorim.AI — Dashboard Routes  (api/routes/dashboard.py)

Implements E-18: GET /api/v1/dashboard/summary per API_CONTRACTS.md §9.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from app.api.deps import get_db
from app.schemas.dashboard import DashboardSummary
from app.services.dashboard_service import get_dashboard_summary

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get(
    "/summary",
    response_model=DashboardSummary,
    summary="Get aggregated ITSM dashboard metrics across all domains",
)
def get_summary(db: Any = Depends(get_db)) -> DashboardSummary:
    return get_dashboard_summary(db)
