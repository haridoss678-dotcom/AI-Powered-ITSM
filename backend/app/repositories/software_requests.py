from __future__ import annotations

from typing import Any


def _collection(db: Any):
    if db is None:
        raise RuntimeError("MongoDB database handle is unavailable.")
    if hasattr(db, "get_collection"):
        collection = db.get_collection("software_requests")
    elif hasattr(db, "__getitem__"):
        try:
            collection = db["software_requests"]
        except KeyError as exc:
            raise RuntimeError("MongoDB collection 'software_requests' is unavailable.") from exc
    else:
        raise RuntimeError("MongoDB collection 'software_requests' is unavailable.")
    if collection is None:
        raise RuntimeError("MongoDB collection 'software_requests' is unavailable.")
    return collection


def insert_request(db: Any, request_doc: dict[str, Any], *, session: Any = None) -> dict[str, Any]:
    collection = _collection(db)
    options = {"session": session} if session is not None else {}
    collection.insert_one(request_doc, **options)
    return request_doc


def get_request(db: Any, request_id: str, *, session: Any = None) -> dict[str, Any] | None:
    collection = _collection(db)
    options = {"session": session} if session is not None else {}
    return collection.find_one({"_id": request_id}, **options)


def update_request(
    db: Any,
    request_id: str,
    patch: dict[str, Any],
    *,
    session: Any = None,
) -> dict[str, Any] | None:
    collection = _collection(db)
    options = {"session": session} if session is not None else {}
    collection.update_one({"_id": request_id}, {"$set": patch}, **options)
    return collection.find_one({"_id": request_id}, **options)


def list_requests(
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
        query["employee.employee_id"] = employee_id
    total = collection.count_documents(query)
    items = list(collection.find(query).sort("created_at", -1).skip(skip).limit(limit))
    return items, total


def count_requests_by_status(db: Any) -> dict[str, int]:
    collection = _collection(db)
    return {
        "submitted": collection.count_documents({"status": "submitted"}),
        "provisioning": collection.count_documents({"status": "provisioning"}),
        "completed": collection.count_documents({"status": "completed"}),
        "failed": collection.count_documents({"status": "failed"}),
    }
