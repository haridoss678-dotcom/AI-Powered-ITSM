from __future__ import annotations

from typing import Any


def _collection(db: Any):
    if db is None:
        raise RuntimeError("MongoDB database handle is unavailable.")
    if hasattr(db, "get_collection"):
        collection = db.get_collection("chat_history")
    elif hasattr(db, "__getitem__"):
        try:
            collection = db["chat_history"]
        except KeyError as exc:
            raise RuntimeError("MongoDB collection 'chat_history' is unavailable.") from exc
    else:
        raise RuntimeError("MongoDB collection 'chat_history' is unavailable.")
    if collection is None:
        raise RuntimeError("MongoDB collection 'chat_history' is unavailable.")
    return collection


def insert_chat_record(db: Any, record: dict[str, Any]) -> dict[str, Any]:
    _collection(db).insert_one(record)
    return record


def get_chat_record(
    db: Any, request_id: str, *, session: Any = None
) -> dict[str, Any] | None:
    options = {"session": session} if session is not None else {}
    return _collection(db).find_one({"_id": request_id}, **options)


def link_ticket_to_chat_record(
    db: Any,
    request_id: str,
    *,
    ticket_id: str,
    session: Any = None,
) -> bool:
    options = {"session": session} if session is not None else {}
    result = _collection(db).update_one(
        {"_id": request_id, "ticket_id": None},
        {"$set": {"ticket_id": ticket_id, "outcome": "ticket_created"}},
        **options,
    )
    return result.matched_count > 0


def list_chat_records(
    db: Any,
    *,
    employee_id: str | None = None,
    entry_type: str | None = None,
    conversation_id: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[dict[str, Any]], int]:
    query: dict[str, Any] = {}
    if employee_id is not None:
        query["employee_id"] = employee_id
    if entry_type is not None:
        query["entry_type"] = entry_type
    if conversation_id is not None:
        query["conversation_id"] = conversation_id
    collection = _collection(db)
    items = list(collection.find(query).sort("created_at", -1).skip(skip).limit(limit))
    return items, collection.count_documents(query)
