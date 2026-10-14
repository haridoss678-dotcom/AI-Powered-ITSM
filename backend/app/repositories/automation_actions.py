from __future__ import annotations

from typing import Any


def _collection(db: Any):
    if db is None:
        raise RuntimeError("MongoDB database handle is unavailable.")
    if hasattr(db, "get_collection"):
        collection = db.get_collection("automation_actions")
    elif hasattr(db, "__getitem__"):
        try:
            collection = db["automation_actions"]
        except KeyError as exc:
            raise RuntimeError("MongoDB collection 'automation_actions' is unavailable.") from exc
    else:
        raise RuntimeError("MongoDB collection 'automation_actions' is unavailable.")
    if collection is None:
        raise RuntimeError("MongoDB collection 'automation_actions' is unavailable.")
    return collection


def insert_action(db: Any, action: dict[str, Any], *, session: Any = None) -> dict[str, Any]:
    collection = _collection(db)
    options = {"session": session} if session is not None else {}
    collection.insert_one(action, **options)
    return action


def get_action(db: Any, action_id: str, *, session: Any = None) -> dict[str, Any] | None:
    collection = _collection(db)
    options = {"session": session} if session is not None else {}
    return collection.find_one({"_id": action_id}, **options)


def update_action(
    db: Any,
    action_id: str,
    patch: dict[str, Any],
    *,
    session: Any = None,
) -> dict[str, Any] | None:
    collection = _collection(db)
    options = {"session": session} if session is not None else {}
    collection.update_one({"_id": action_id}, {"$set": patch}, **options)
    return collection.find_one({"_id": action_id}, **options)


def list_actions(
    db: Any,
    *,
    status: str | None = None,
    employee_id: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[dict[str, Any]], int]:
    collection = _collection(db)
    query: dict[str, Any] = {}
    if status is not None:
        query["status"] = status
    if employee_id is not None:
        query["employee_id"] = employee_id
    total = collection.count_documents(query)
    items = list(collection.find(query).sort("started_at", -1).skip(skip).limit(limit))
    return items, total


def count_actions_by_status(db: Any) -> dict[str, int]:
    collection = _collection(db)
    counts = {
        "succeeded": collection.count_documents({"status": "succeeded"}),
        "failed": collection.count_documents({"status": "failed"}),
        "validation_failed": collection.count_documents({"status": "validation_failed"}),
        "skipped_ineligible": collection.count_documents({"status": "skipped_ineligible"}),
    }
    return counts
