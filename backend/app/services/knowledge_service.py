"""
Sorim.AI — Knowledge Base Service  (services/knowledge_service.py)

Façade for article listing, article details, semantic search, and ingestion.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.ai.rag.embedding_service import get_embedding_service
from app.ai.rag.ingestion import load_and_chunk_article
from app.ai.rag.rag_pipeline import get_rag_pipeline
from app.ai.rag.vector_store import get_vector_store
from app.core.config import get_settings
from app.core.errors import AppError, ErrorCode
from app.repositories.knowledge_metadata import (
    get_article_metadata,
    list_articles_metadata,
    upsert_article_metadata,
)
from app.schemas.common import Page
from app.schemas.knowledge import (
    ArticleDetail,
    ArticleSummary,
    KnowledgeSearchResponse,
)


def _resolve_knowledge_dir() -> Path:
    repo_root = Path(__file__).resolve().parents[3]
    candidate = repo_root / "knowledge_base"
    if candidate.is_dir():
        return candidate
    return Path(get_settings().knowledge_base_dir).resolve()


def ingest_knowledge_base(db: Any) -> dict[str, Any]:
    kb_dir = _resolve_knowledge_dir()
    if not kb_dir.is_dir():
        return {"ingested_count": 0, "articles": []}

    embedding_service = get_embedding_service()
    vector_store = get_vector_store()
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    ingested_articles: list[str] = []
    for md_file in sorted(kb_dir.glob("*.md")):
        metadata, chunks, raw_content = load_and_chunk_article(md_file)
        article_id = metadata["article_id"]

        # Embed all chunks
        chunk_texts = [c["text"] for c in chunks]
        embeddings = embedding_service.embed_texts(chunk_texts)
        chunk_ids = [c["chunk_id"] for c in chunks]
        chunk_metadatas = [
            {
                "article_id": c["article_id"],
                "chunk_index": c["chunk_index"],
                "title": c["title"],
                "category": c["category"],
                "source_file": c["source_file"],
                "content_hash": c["content_hash"],
                "excerpt": c["excerpt"],
            }
            for c in chunks
        ]

        # Update vector store
        vector_store.delete(where={"article_id": article_id})
        vector_store.add(
            ids=chunk_ids,
            embeddings=embeddings,
            metadatas=chunk_metadatas,
            documents=chunk_texts,
        )

        metadata["embedding_model_id"] = get_settings().embedding_model_id
        metadata["ingested_at"] = now_iso
        upsert_article_metadata(db, metadata)
        ingested_articles.append(article_id)

    return {"ingested_count": len(ingested_articles), "articles": ingested_articles}


def list_articles(
    db: Any,
    category: str | None = None,
    *,
    skip: int = 0,
    limit: int = 50,
) -> Page[ArticleSummary]:
    items, total = list_articles_metadata(db, category, skip=skip, limit=limit)
    if total == 0:
        # Auto-ingest if metadata collection is empty
        ingest_knowledge_base(db)
        items, total = list_articles_metadata(db, category, skip=skip, limit=limit)

    summaries = [
        ArticleSummary(
            article_id=it["_id"],
            title=it.get("title", ""),
            category=it.get("category", ""),
            tags=it.get("tags", []),
            summary=it.get("summary", ""),
            automations=it.get("automations", []),
            source_file=it.get("source_file", ""),
            chunk_count=it.get("chunk_count", 1),
            ingested_at=it.get("ingested_at", datetime.now(timezone.utc).isoformat()),
        )
        for it in items
    ]
    return Page(items=summaries, total=total, limit=limit, skip=skip)


def get_article(db: Any, article_id: str) -> ArticleDetail:
    meta = get_article_metadata(db, article_id)
    if meta is None:
        # Check if articles need initial ingestion
        ingest_knowledge_base(db)
        meta = get_article_metadata(db, article_id)

    if meta is None:
        raise AppError(
            code=ErrorCode.NOT_FOUND,
            message=f"Knowledge article '{article_id}' was not found.",
            http_status=404,
        )

    kb_dir = _resolve_knowledge_dir()
    source_file = meta.get("source_file") or f"{article_id}.md"
    file_path = kb_dir / source_file

    if not file_path.is_file():
        raise AppError(
            code=ErrorCode.NOT_FOUND,
            message=f"Knowledge article file for '{article_id}' could not be located.",
            http_status=404,
        )

    content = file_path.read_text(encoding="utf-8")
    return ArticleDetail(
        article_id=meta["_id"],
        title=meta.get("title", ""),
        category=meta.get("category", ""),
        tags=meta.get("tags", []),
        summary=meta.get("summary", ""),
        automations=meta.get("automations", []),
        source_file=source_file,
        chunk_count=meta.get("chunk_count", 1),
        ingested_at=meta.get("ingested_at", datetime.now(timezone.utc).isoformat()),
        content_markdown=content,
    )


def search_knowledge(
    db: Any,
    query: str,
    *,
    top_k: int = 4,
    mode: str = "retrieve",
    category: str | None = None,
) -> KnowledgeSearchResponse:
    # Ensure vector store is seeded with knowledge articles
    vector_store = get_vector_store()
    if hasattr(vector_store, "count") and vector_store.count() == 0:
        ingest_knowledge_base(db)

    pipeline = get_rag_pipeline()
    return pipeline.search_and_answer(query, top_k=top_k, mode=mode, category=category)
