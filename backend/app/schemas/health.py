"""
Sorim.AI — Health Endpoint Schemas  (schemas/health.py)

Matches the API_CONTRACTS.md E-01 response exactly:
{
  "status": "ok" | "error",
  "version": str,
  "timestamp": str,
  "checks": {
    "database": Check,
    "vector_store": Check,
    "llm": Check,
    "embedding_model": Check,
    "servicenow": Check
  }
}

Phase 1 reports only "database"; others are "not_configured".
"""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel


class Check(BaseModel):
    status: Literal["ok", "error", "not_configured"]
    detail: Optional[str] = None
    latency_ms: Optional[int] = None
    meta: Optional[Any] = None


class HealthChecks(BaseModel):
    database: Check
    vector_store: Check = Check(status="not_configured")
    llm: Check = Check(status="not_configured")
    embedding_model: Check = Check(status="not_configured")
    servicenow: Check = Check(status="not_configured")


class HealthResponse(BaseModel):
    status: Literal["ok", "error"]
    version: str
    timestamp: str
    checks: HealthChecks
