"""
Sorim.AI — Audit Log Schemas  (schemas/audit.py)

Pydantic schemas matching API_CONTRACTS.md §1.10, §7 and DATA_MODEL.md §3.7.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import Actor, AuditOutcome


class AuditLog(BaseModel):
    model_config = ConfigDict(extra="forbid")

    audit_id: str
    timestamp: str
    actor: Actor
    event_type: str
    outcome: AuditOutcome
    request_id: str | None = None
    entity_type: str | None = None
    entity_id: str | None = None
    mode: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)
