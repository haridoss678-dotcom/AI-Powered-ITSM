from __future__ import annotations

from typing import Any


def _collection(db: Any):
    if db is None:
        raise RuntimeError("MongoDB database handle is unavailable.")
    if hasattr(db, "get_collection"):
        collection = db.get_collection("knowledge_metadata")
    elif hasattr(db, "__getitem__"):
        try:
            collection = db["knowledge_metadata"]
        except KeyError as exc:
            raise RuntimeError("MongoDB collection 'knowledge_metadata' is unavailable.") from exc
    else:
        raise RuntimeError("MongoDB collection 'knowledge_metadata' is unavailable.")
    if collection is None:
        raise RuntimeError("MongoDB collection 'knowledge_metadata' is unavailable.")
    return collection


def upsert_article_metadata(db: Any, metadata: dict[str, Any], *, session: Any = None) -> dict[str, Any]:
    collection = _collection(db)
    options = {"session": session} if session is not None else {}
    doc = dict(metadata)
    article_id = doc["_id"]
    collection.find_one_and_update(
        {"_id": article_id},
        {"$set": doc},
        upsert=True,
        **options,
    )
    return doc


def get_article_metadata(db: Any, article_id: str, *, session: Any = None) -> dict[str, Any] | None:
    collection = _collection(db)
    options = {"session": session} if session is not None else {}
    return collection.find_one({"_id": article_id}, **options)


def list_articles_metadata(
    db: Any,
    category: str | None = None,
    *,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[dict[str, Any]], int]:
    collection = _collection(db)
    query: dict[str, Any] = {}
    if category is not None:
        query["category"] = category
    total = collection.count_documents(query)
    items = list(collection.find(query).sort("_id", 1).skip(skip).limit(limit))
    return items, total
