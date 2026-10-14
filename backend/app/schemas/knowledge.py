"""
Sorim.AI — Knowledge Base Schemas  (schemas/knowledge.py)

Pydantic schemas matching API_CONTRACTS.md §1.11, §5 and DATA_MODEL.md §3.3.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.analysis import Confidence, Escalation, Timings


class ArticleSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    article_id: str
    title: str
    category: str
    tags: list[str] = Field(default_factory=list)
    summary: str
    automations: list[str] = Field(default_factory=list)
    source_file: str
    chunk_count: int
    ingested_at: str


class ArticleDetail(ArticleSummary):
    content_markdown: str


class Source(BaseModel):
    model_config = ConfigDict(extra="forbid")

    article_id: str
    title: str
    category: str
    chunk_id: str
    chunk_index: int
    score: float = Field(ge=0.0, le=1.0)
    excerpt: str = Field(max_length=400)
    cited: bool = False


class SearchHit(Source):
    text: str


class KnowledgeSearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1, max_length=500)
    top_k: int = Field(default=4, ge=1, le=10)
    mode: Literal["retrieve", "answer"] = "retrieve"
    category: str | None = None


class KnowledgeSearchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str
    mode: str
    hits: list[SearchHit]
    answer: str | None = None
    insufficient_knowledge: bool = False
    confidence: Confidence | None = None
    escalation: Escalation
    timings_ms: Timings
