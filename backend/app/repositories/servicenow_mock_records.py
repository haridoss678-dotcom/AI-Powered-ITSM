from __future__ import annotations

from typing import Any, Optional


def _collection(db: Any):
    if db is None:
        raise RuntimeError("MongoDB database handle is unavailable.")
    if hasattr(db, "get_collection"):
        collection = db.get_collection("servicenow_mock_records")
    elif hasattr(db, "__getitem__"):
        try:
            collection = db["servicenow_mock_records"]
        except KeyError as exc:
            raise RuntimeError("MongoDB collection 'servicenow_mock_records' is unavailable.") from exc
    else:
        raise RuntimeError("MongoDB collection 'servicenow_mock_records' is unavailable.")
    if collection is None:
        raise RuntimeError("MongoDB collection 'servicenow_mock_records' is unavailable.")
    return collection


def create_record(db: Any, record: dict, *, session: Any = None) -> dict:
    collection = _collection(db)
    options = {"session": session} if session is not None else {}
    collection.insert_one(record, **options)
    return record


def get_record(db: Any, sys_id: str) -> Optional[dict]:
    collection = _collection(db)
    return collection.find_one({"_id": sys_id})


def update_record(db: Any, sys_id: str, patch: dict) -> Optional[dict]:
    collection = _collection(db)
    collection.update_one({"_id": sys_id}, {"$set": patch})
    return collection.find_one({"_id": sys_id})
