"""
Sorim.AI — Semantic Retriever  (ai/rag/retriever.py)

Performs query embedding and semantic search against the vector store.
"""

from __future__ import annotations

from typing import Any

from app.core.errors import AppError, ErrorCode
from app.ai.rag.embedding_service import get_embedding_service
from app.ai.rag.vector_store import get_vector_store
from app.schemas.knowledge import SearchHit


class SemanticRetriever:
    def __init__(self) -> None:
        self.embedding_service = get_embedding_service()

    def retrieve(
        self,
        query: str,
        *,
        top_k: int = 4,
        category: str | None = None,
    ) -> list[SearchHit]:
        try:
            query_emb = self.embedding_service.embed_text(query)
            collection = get_vector_store()
            where = {"category": category} if category else None

            results = collection.query(
                query_embeddings=[query_emb],
                n_results=top_k,
                where=where,
            )
        except AppError:
            raise
        except Exception as exc:
            raise AppError(
                code=ErrorCode.RETRIEVAL_UNAVAILABLE,
                message="Knowledge retrieval service is unavailable.",
                http_status=503,
            ) from exc

        hits: list[SearchHit] = []
        ids = results.get("ids", [[]])[0]
        distances = results.get("distances", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        documents = results.get("documents", [[]])[0]

        for chunk_id, dist, meta, doc in zip(ids, distances, metadatas, documents):
            # Cosine distance: score = 1.0 - distance
            score = round(max(0.0, min(1.0, 1.0 - float(dist))), 4)
            excerpt = meta.get("excerpt") or doc[:300]
            hits.append(
                SearchHit(
                    article_id=meta.get("article_id", ""),
                    title=meta.get("title", ""),
                    category=meta.get("category", ""),
                    chunk_id=chunk_id,
                    chunk_index=int(meta.get("chunk_index", 1)),
                    score=score,
                    excerpt=excerpt[:300],
                    cited=False,
                    text=doc,
                )
            )

        return hits


_retriever = SemanticRetriever()


def get_retriever() -> SemanticRetriever:
    return _retriever
