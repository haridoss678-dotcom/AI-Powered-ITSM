from __future__ import annotations

from typing import Any


def _collection(db: Any):
    if db is None:
        raise RuntimeError("MongoDB database handle is unavailable.")
    if hasattr(db, "get_collection"):
        collection = db.get_collection("audit_logs")
    elif hasattr(db, "__getitem__"):
        try:
            collection = db["audit_logs"]
        except KeyError as exc:
            raise RuntimeError("MongoDB collection 'audit_logs' is unavailable.") from exc
    else:
        raise RuntimeError("MongoDB collection 'audit_logs' is unavailable.")
    if collection is None:
        raise RuntimeError("MongoDB collection 'audit_logs' is unavailable.")
    return collection


def insert_event(db: Any, event: dict, *, session: Any = None) -> dict:
    collection = _collection(db)
    options = {"session": session} if session is not None else {}
    collection.insert_one(event, **options)
    return event


def list_events(db: Any, limit: int = 50) -> list[dict]:
    collection = _collection(db)
    return list(collection.find({}).sort("timestamp", -1).limit(limit))


def query_events(
    db: Any,
    *,
    request_id: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    event_type: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[dict], int]:
    collection = _collection(db)
    query: dict[str, Any] = {}
    if request_id is not None:
        query["request_id"] = request_id
    if entity_type is not None:
        query["entity_type"] = entity_type
    if entity_id is not None:
        query["entity_id"] = entity_id
    if event_type is not None:
        query["event_type"] = event_type
    total = collection.count_documents(query)
    items = list(collection.find(query).sort("timestamp", -1).skip(skip).limit(limit))
    return items, total
