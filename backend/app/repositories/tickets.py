from __future__ import annotations

from typing import Any, Optional


def _collection(db: Any):
    if db is None:
        raise RuntimeError("MongoDB database handle is unavailable.")
    if hasattr(db, "get_collection"):
        collection = db.get_collection("tickets")
    elif hasattr(db, "__getitem__"):
        try:
            collection = db["tickets"]
        except KeyError as exc:
            raise RuntimeError("MongoDB collection 'tickets' is unavailable.") from exc
    else:
        raise RuntimeError("MongoDB collection 'tickets' is unavailable.")
    if collection is None:
        raise RuntimeError("MongoDB collection 'tickets' is unavailable.")
    return collection


def insert_ticket(db: Any, ticket: dict, *, session: Any = None) -> dict:
    collection = _collection(db)
    options = {"session": session} if session is not None else {}
    collection.insert_one(ticket, **options)
    return ticket


def get_ticket(db: Any, ticket_id: str) -> Optional[dict]:
    collection = _collection(db)
    return collection.find_one({"_id": ticket_id})


def list_tickets(
    db: Any,
    *,
    status: Optional[str] = None,
    escalated: Optional[bool] = None,
    employee_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[dict], int]:
    collection = _collection(db)
    query: dict[str, Any] = {}
    if status is not None:
        query["status"] = status
    if escalated is not None:
        query["escalated"] = escalated
    if employee_id is not None:
        query["requester.employee_id"] = employee_id

    items = list(collection.find(query).sort("created_at", -1).skip(skip).limit(limit))
    total = collection.count_documents(query)
    return items, total


def update_ticket(db: Any, ticket_id: str, patch: dict) -> Optional[dict]:
    collection = _collection(db)
    collection.update_one({"_id": ticket_id}, {"$set": patch})
    return collection.find_one({"_id": ticket_id})


def find_by_request_id(
    db: Any, request_id: str, *, session: Any = None
) -> Optional[dict]:
    collection = _collection(db)
    options = {"session": session} if session is not None else {}
    return collection.find_one({"request_id": request_id}, **options)
