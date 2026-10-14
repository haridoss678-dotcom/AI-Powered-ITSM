from __future__ import annotations

import re
from typing import Any

from pymongo import ReturnDocument

_COLLECTION_PREFIXES: dict[str, tuple[str, str, str]] = {
    "ticket": ("tickets", "TKT-", "ticket_id"),
    "audit": ("audit_logs", "AUD-", "_id"),
    "automation_action": ("automation_actions", "ACT-", "action_id"),
    "software_request": ("software_requests", "SWR-", "software_request_id"),
    "ai_request": ("chat_history", "AIR-", "request_id"),
    "conversation": ("chat_history", "CNV-", "conversation_id"),
    "employee": ("users", "EMP-", "_id"),
}


def _collection(db: Any):
    if db is None:
        raise RuntimeError("MongoDB database handle is unavailable.")
    if hasattr(db, "get_collection"):
        collection = db.get_collection("counters")
    elif hasattr(db, "__getitem__"):
        try:
            collection = db["counters"]
        except KeyError as exc:
            raise RuntimeError("MongoDB collection 'counters' is unavailable.") from exc
    else:
        raise RuntimeError("MongoDB collection 'counters' is unavailable.")
    if collection is None:
        raise RuntimeError("MongoDB collection 'counters' is unavailable.")
    return collection


def _get_existing_max_id(db: Any, name: str) -> int:
    target_info = _COLLECTION_PREFIXES.get(name)
    if not target_info:
        return 0
    coll_name, prefix, id_field = target_info
    try:
        coll = None
        if hasattr(db, "get_collection"):
            coll = db.get_collection(coll_name)
        elif hasattr(db, "__getitem__"):
            coll = db[coll_name]
        if coll is None:
            return 0

        max_num = 0
        pattern = re.compile(rf"^{re.escape(prefix)}(\d+)$")
        # Inspect docs in the collection to detect pre-existing max sequence number
        for doc in coll.find():
            for field in (id_field, "_id"):
                val = doc.get(field)
                if isinstance(val, str):
                    m = pattern.match(val)
                    if m:
                        max_num = max(max_num, int(m.group(1)))
        return max_num
    except Exception:
        return 0


def get_next_sequence(db: Any, name: str, *, session: Any = None) -> int:
    collection = _collection(db)
    options = {"session": session} if session is not None else {}

    # Detect if the counter document does not exist yet
    existing = collection.find_one({"_id": name}, **options)
    if existing is None:
        # Check for plural legacy counter in counters collection (e.g. 'tickets')
        legacy = collection.find_one({"_id": f"{name}s"}, **options)
        legacy_val = 0
        if legacy:
            legacy_val = int(legacy.get("seq") or legacy.get("value") or 0)

        # Check actual target collection for existing max id
        max_target = _get_existing_max_id(db, name)
        initial_val = max(legacy_val, max_target)
        if initial_val > 0:
            collection.update_one(
                {"_id": name},
                {"$set": {"seq": initial_val}},
                upsert=True,
                **options,
            )

    doc = collection.find_one_and_update(
        {"_id": name},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
        **options,
    )
    if doc is None or "seq" not in doc:
        raise RuntimeError("MongoDB sequence update did not return a sequence value.")
    return int(doc["seq"])
