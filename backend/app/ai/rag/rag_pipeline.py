"""
Sorim.AI — RAG Pipeline Coordinator  (ai/rag/rag_pipeline.py)

Orchestrates semantic retrieval, threshold filtering, grounded answer generation,
confidence evaluation, and escalation decisions.
"""

from __future__ import annotations

import time

from app.ai.rag.answer_generator import generate_grounded_answer
from app.ai.rag.retriever import get_retriever
from app.ai.safety.confidence import compute_confidence
from app.ai.safety.escalation import determine_escalation
from app.schemas.analysis import Timings
from app.schemas.common import EscalationReason
from app.schemas.knowledge import KnowledgeSearchResponse, SearchHit

RETRIEVAL_MIN_SCORE = 0.20
INSUFFICIENT_KNOWLEDGE_MESSAGE = (
    "The requested information is not available in the approved corporate knowledge base. "
    "Please create an incident ticket or contact human IT support for assistance."
)


class RAGPipeline:
    def __init__(self) -> None:
        self.retriever = get_retriever()

    def retrieve(
        self,
        query: str,
        *,
        top_k: int = 4,
        category: str | None = None,
    ) -> list[SearchHit]:
        return self.retriever.retrieve(query, top_k=top_k, category=category)

    def search_and_answer(
        self,
        query: str,
        *,
        top_k: int = 4,
        mode: str = "retrieve",
        category: str | None = None,
    ) -> KnowledgeSearchResponse:
        start_time = time.monotonic()
        retrieval_start = time.monotonic()
        hits = self.retrieve(query, top_k=top_k, category=category)
        retrieval_ms = int((time.monotonic() - retrieval_start) * 1000)

        # Check retrieval quality against minimum threshold
        top_score = hits[0].score if hits else 0.0
        insufficient_knowledge = (not hits) or (top_score < RETRIEVAL_MIN_SCORE)

        if mode == "retrieve":
            total_ms = int((time.monotonic() - start_time) * 1000)
            escalation = determine_escalation(
                required=insufficient_knowledge,
                reason=EscalationReason.insufficient_knowledge if insufficient_knowledge else None,
                message=INSUFFICIENT_KNOWLEDGE_MESSAGE if insufficient_knowledge else None,
            )
            return KnowledgeSearchResponse(
                query=query,
                mode=mode,
                hits=hits,
                answer=None,
                insufficient_knowledge=insufficient_knowledge,
                confidence=None,
                escalation=escalation,
                timings_ms=Timings(
                    analysis=None,
                    retrieval=retrieval_ms,
                    generation=None,
                    total=total_ms,
                ),
            )

        # Mode == "answer"
        gen_start = time.monotonic()
        if insufficient_knowledge:
            gen_ms = int((time.monotonic() - gen_start) * 1000)
            total_ms = int((time.monotonic() - start_time) * 1000)
            confidence = compute_confidence(retrieval_top_score=top_score, grounding_score=0.0)
            escalation = determine_escalation(
                required=True,
                reason=EscalationReason.insufficient_knowledge,
                message=INSUFFICIENT_KNOWLEDGE_MESSAGE,
            )
            return KnowledgeSearchResponse(
                query=query,
                mode=mode,
                hits=hits,
                answer=INSUFFICIENT_KNOWLEDGE_MESSAGE,
                insufficient_knowledge=True,
                confidence=confidence,
                escalation=escalation,
                timings_ms=Timings(
                    analysis=None,
                    retrieval=retrieval_ms,
                    generation=gen_ms,
                    total=total_ms,
                ),
            )

        answer, is_insufficient, updated_hits, grounding_score = generate_grounded_answer(query, hits)
        gen_ms = int((time.monotonic() - gen_start) * 1000)
        total_ms = int((time.monotonic() - start_time) * 1000)

        if is_insufficient:
            confidence = compute_confidence(retrieval_top_score=top_score, grounding_score=0.0)
            escalation = determine_escalation(
                required=True,
                reason=EscalationReason.insufficient_knowledge,
                message=INSUFFICIENT_KNOWLEDGE_MESSAGE,
            )
            return KnowledgeSearchResponse(
                query=query,
                mode=mode,
                hits=updated_hits,
                answer=INSUFFICIENT_KNOWLEDGE_MESSAGE,
                insufficient_knowledge=True,
                confidence=confidence,
                escalation=escalation,
                timings_ms=Timings(
                    analysis=None,
                    retrieval=retrieval_ms,
                    generation=gen_ms,
                    total=total_ms,
                ),
            )

        confidence = compute_confidence(
            retrieval_top_score=top_score,
            grounding_score=grounding_score,
        )
        escalation = determine_escalation(
            required=confidence.below_threshold,
            reason=EscalationReason.low_confidence if confidence.below_threshold else None,
            message="Confidence is below optimal threshold; human review recommended." if confidence.below_threshold else None,
        )

        return KnowledgeSearchResponse(
            query=query,
            mode=mode,
            hits=updated_hits,
            answer=answer,
            insufficient_knowledge=False,
            confidence=confidence,
            escalation=escalation,
            timings_ms=Timings(
                analysis=None,
                retrieval=retrieval_ms,
                generation=gen_ms,
                total=total_ms,
            ),
        )


_rag_pipeline = RAGPipeline()


def get_rag_pipeline() -> RAGPipeline:
    return _rag_pipeline
