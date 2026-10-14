from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.repositories.audit_logs import insert_event
from app.repositories.sequences import get_next_sequence


def log_audit_event(
    db: Any,
    *,
    actor: str,
    event_type: str,
    outcome: str,
    details: dict[str, Any] | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    request_id: str | None = None,
    mode: str | None = "mock",
    session: Any = None,
) -> dict[str, Any]:
    event = {
        "_id": f"AUD-{get_next_sequence(db, 'audit', session=session):06d}",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "actor": actor,
        "event_type": event_type,
        "outcome": outcome,
        "request_id": request_id,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "mode": mode,
        "details": details or {},
    }
    insert_event(db, event, session=session)
    return event
