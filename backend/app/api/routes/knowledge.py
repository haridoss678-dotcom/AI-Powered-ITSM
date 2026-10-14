"""
Sorim.AI — Knowledge Base Routes  (api/routes/knowledge.py)

Implements E-07, E-08, E-09 per API_CONTRACTS.md §5.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_db
from app.schemas.common import Page
from app.schemas.knowledge import (
    ArticleDetail,
    ArticleSummary,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
)
from app.services import knowledge_service

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get(
    "/articles",
    response_model=Page[ArticleSummary],
    summary="List approved knowledge base articles",
)
def list_articles(
    category: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    skip: int = Query(default=0, ge=0),
    db: Any = Depends(get_db),
) -> Page[ArticleSummary]:
    return knowledge_service.list_articles(db, category=category, skip=skip, limit=limit)


@router.get(
    "/articles/{article_id}",
    response_model=ArticleDetail,
    summary="Get full article details with markdown content",
)
def get_article(
    article_id: str,
    db: Any = Depends(get_db),
) -> ArticleDetail:
    return knowledge_service.get_article(db, article_id=article_id)


@router.post(
    "/search",
    response_model=KnowledgeSearchResponse,
    summary="Semantic retrieval and grounded answer generation",
)
def search_knowledge(
    payload: KnowledgeSearchRequest,
    db: Any = Depends(get_db),
) -> KnowledgeSearchResponse:
    return knowledge_service.search_knowledge(
        db,
        query=payload.query,
        top_k=payload.top_k,
        mode=payload.mode,
        category=payload.category,
    )
