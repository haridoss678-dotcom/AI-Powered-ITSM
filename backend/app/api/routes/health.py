"""
Sorim.AI — Health Endpoint  (api/routes/health.py)

Implements E-01: GET /health  (API_CONTRACTS.md §3)

Phase 3 behavior:
  - Runs a read-only ping against MongoDB Atlas.
  - Reports the local model readiness without loading it or downloading weights.
  - Returns 503 if either configured dependency check fails.

This endpoint is NOT behind authentication. It must never reveal credentials,
stack traces, or internal connection strings.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

import app.db.mongo as mongo
from app.ai.llm.llm_service import health_status as llm_health_status
from app.ai.rag.embedding_service import get_embedding_service
from app.ai.rag.vector_store import get_vector_manager
from app.core.config import get_settings
from app.schemas.health import Check, HealthChecks, HealthResponse

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="Application health and readiness check",
    description=(
        "Returns the liveness and readiness status of the application and its dependencies. "
        "Phase 1: only database connectivity is checked. "
        "Returns 200 when all configured checks pass; 503 otherwise. "
        "The response body shape is identical for both status codes."
    ),
    response_model=HealthResponse,
    responses={
        200: {"description": "All configured checks passed."},
        503: {"description": "One or more configured checks failed."},
    },
)
async def health_check() -> JSONResponse:
    """
    E-01 — GET /api/v1/health

    Side effects: one read-only MongoDB admin ping only.
    No writes, no collection creation, no business records.
    """
    settings = get_settings()
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    # ── Database check ───────────────────────────────────────────────────────
    db_result = mongo.check_db_connectivity()
    db_check = Check(
        status="ok" if db_result.ok else "error",
        detail=db_result.detail,
        latency_ms=db_result.latency_ms,
    )

    # ── Model readiness is an observation only; health never loads or downloads it. ──
    llm_check = Check(**llm_health_status())
    vector_store_check = Check(**get_vector_manager().health_status())
    embedding_check = Check(**get_embedding_service().health_status())
    servicenow_check = Check(
        status="ok",
        meta={"mode": settings.servicenow_mode},
    )

    checks = HealthChecks(
        database=db_check,
        vector_store=vector_store_check,
        llm=llm_check,
        embedding_model=embedding_check,
        servicenow=servicenow_check,
    )

    # Unconfigured future checks do not fail readiness; the database and Phase 3
    # local model are configured dependencies and must both be ready.
    overall_ok = db_check.status == "ok" and llm_check.status == "ok"
    overall_status = "ok" if overall_ok else "error"

    response_body = HealthResponse(
        status=overall_status,
        version=settings.app_version,
        timestamp=timestamp,
        checks=checks,
    )

    http_status = status.HTTP_200_OK if overall_ok else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(
        status_code=http_status,
        content=response_body.model_dump(),
    )
