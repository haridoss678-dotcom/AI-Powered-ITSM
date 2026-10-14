"""
Sorim.AI — Chroma Vector Store & Fallback  (ai/rag/vector_store.py)

Manages persistent vector collection knowledge_chunks using Chroma or
an in-process cosine vector store if chromadb is not installed.
"""

from __future__ import annotations

import importlib.util
import math
from pathlib import Path
from typing import Any

from app.core.config import get_settings


def _cosine_distance(vec_a: list[float], vec_b: list[float]) -> float:
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0 or norm_b == 0:
        return 1.0
    similarity = dot / (norm_a * norm_b)
    similarity = max(-1.0, min(1.0, similarity))
    return max(0.0, 1.0 - similarity)


class LocalVectorCollection:
    """In-process persistent vector collection mimicking Chroma Collection."""

    def __init__(self, name: str) -> None:
        self.name = name
        self._items: dict[str, dict[str, Any]] = {}
        self._persist_file = Path(get_settings().chroma_persist_dir).resolve() / "knowledge_chunks_local.json"
        self._load()

    def _load(self) -> None:
        if self._persist_file.exists():
            try:
                import json
                data = json.loads(self._persist_file.read_text(encoding="utf-8"))
                self._items = data
            except Exception:
                pass

    def _save(self) -> None:
        try:
            import json
            self._persist_file.parent.mkdir(parents=True, exist_ok=True)
            self._persist_file.write_text(json.dumps(self._items, default=str), encoding="utf-8")
        except Exception:
            pass

    def add(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
        documents: list[str],
    ) -> None:
        for doc_id, emb, meta, doc in zip(ids, embeddings, metadatas, documents):
            self._items[doc_id] = {
                "id": doc_id,
                "embedding": emb,
                "metadata": meta,
                "document": doc,
            }
        self._save()

    def delete(self, ids: list[str] | None = None, where: dict[str, Any] | None = None) -> None:
        if ids:
            for doc_id in ids:
                self._items.pop(doc_id, None)
        if where:
            to_del = [
                doc_id
                for doc_id, item in self._items.items()
                if all(item["metadata"].get(k) == v for k, v in where.items())
            ]
            for doc_id in to_del:
                self._items.pop(doc_id, None)
        self._save()

    def count(self) -> int:
        return len(self._items)

    def query(
        self,
        query_embeddings: list[list[float]],
        n_results: int = 4,
        where: dict[str, Any] | None = None,
    ) -> dict[str, list[list[Any]]]:
        if not query_embeddings or not self._items:
            return {"ids": [[]], "distances": [[]], "metadatas": [[]], "documents": [[]]}

        query_emb = query_embeddings[0]
        scored: list[tuple[float, dict[str, Any]]] = []

        for item in self._items.values():
            if where:
                match = all(item["metadata"].get(k) == v for k, v in where.items())
                if not match:
                    continue
            dist = _cosine_distance(query_emb, item["embedding"])
            scored.append((dist, item))

        scored.sort(key=lambda x: x[0])
        top = scored[:n_results]

        return {
            "ids": [[item["id"] for _, item in top]],
            "distances": [[dist for dist, _ in top]],
            "metadatas": [[item["metadata"] for _, item in top]],
            "documents": [[item["document"] for _, item in top]],
        }


class VectorStoreManager:
    def __init__(self) -> None:
        self._collection: Any = None
        self._using_chroma: bool = False

    def is_chroma_installed(self) -> bool:
        return importlib.util.find_spec("chromadb") is not None

    def get_collection(self) -> Any:
        if self._collection is not None:
            return self._collection

        settings = get_settings()
        if self.is_chroma_installed():
            try:
                import chromadb
                persist_path = Path(settings.chroma_persist_dir).resolve()
                persist_path.mkdir(parents=True, exist_ok=True)
                client = chromadb.PersistentClient(path=str(persist_path))
                self._collection = client.get_or_create_collection(
                    name="knowledge_chunks",
                    metadata={"hnsw:space": "cosine"},
                )
                self._using_chroma = True
                return self._collection
            except Exception:
                pass

        self._collection = LocalVectorCollection("knowledge_chunks")
        self._using_chroma = False
        return self._collection

    def health_status(self) -> dict[str, Any]:
        coll = self.get_collection()
        count = coll.count() if hasattr(coll, "count") else 0
        return {
            "status": "ok" if self._using_chroma else "not_configured",
            "meta": {
                "collection": "knowledge_chunks",
                "chromadb_installed": self._using_chroma,
                "document_count": count,
            },
        }


_vector_manager = VectorStoreManager()


def get_vector_store() -> Any:
    return _vector_manager.get_collection()


def get_vector_manager() -> VectorStoreManager:
    return _vector_manager
