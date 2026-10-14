"""
Sorim.AI — RAG Answer Generator  (ai/rag/answer_generator.py)

Builds grounded prompt with numbered context and generates grounded answers
with verified citation markers.
"""

from __future__ import annotations

import re
from typing import Any

from app.ai.llm import llm_service
from app.ai.safety.grounding import compute_grounding_score
from app.schemas.knowledge import SearchHit

INSUFFICIENT_CONTEXT_TOKEN = "INSUFFICIENT_CONTEXT"

SYSTEM_PROMPT = """You are Sorim.AI, an enterprise IT Helpdesk Virtual Assistant.
Answer the employee's IT question using ONLY the provided numbered context passages.
Rules:
1. Do not invent or assume any information not present in the context.
2. If the context does not contain sufficient facts to answer the question completely and reliably, respond ONLY with: INSUFFICIENT_CONTEXT
3. Cite your sources inline using bracketed numbers like [1] or [2] corresponding to the relevant passage.
4. Keep the answer clear, professional, and actionable.
"""


def format_context_prompt(hits: list[SearchHit]) -> str:
    parts: list[str] = []
    for idx, hit in enumerate(hits, start=1):
        parts.append(f"[{idx}] Title: {hit.title} ({hit.category})\n{hit.text}")
    return "\n\n".join(parts)


def generate_grounded_answer(
    question: str,
    hits: list[SearchHit],
) -> tuple[str | None, bool, list[SearchHit], float]:
    """
    Returns (answer, is_insufficient, updated_hits_with_citations, grounding_score).
    """
    if not hits:
        return None, True, hits, 0.0

    _STOPWORDS = {
        "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
        "any", "are", "as", "at", "be", "because", "been", "before", "being",
        "below", "between", "both", "but", "by", "can", "cannot", "could", "did", "do",
        "does", "doing", "don't", "down", "during", "each", "few", "for", "from", "further",
        "had", "has", "have", "having", "he", "her", "here", "him", "his", "how", "i",
        "if", "in", "into", "is", "it", "its", "just", "me", "more", "most", "my",
        "no", "nor", "not", "now", "of", "off", "on", "once", "only", "or", "other",
        "our", "out", "over", "own", "same", "she", "should", "so", "some", "such",
        "than", "that", "the", "their", "them", "then", "there", "these", "they", "this",
        "those", "through", "to", "too", "under", "until", "up", "very", "was", "we",
        "were", "what", "when", "where", "which", "while", "who", "whom", "why", "with",
        "would", "you", "your",
    }
    q_words = {w for w in re.findall(r"[a-z0-9_-]{3,}", question.lower()) if w not in _STOPWORDS}
    doc_words = set(re.findall(r"[a-z0-9_-]{3,}", " ".join(h.text for h in hits).lower()))
    if q_words and not (q_words & doc_words):
        return None, True, hits, 0.0

    context_str = format_context_prompt(hits)
    user_prompt = f"Question: {question}\n\nContext:\n{context_str}"

    raw_answer: str | None = None
    try:
        raw_answer = llm_service.generate(
            SYSTEM_PROMPT,
            user_prompt,
            max_new_tokens=256,
        )
    except Exception:
        # If the local LLM is not loaded, construct a grounded extractive answer from top hit
        top = hits[0]
        sentences = [s.strip() for s in top.text.split("\n") if s.strip() and not s.startswith("#")]
        actionable = [s for s in sentences if any(w in s.lower() for w in ("step", "check", "verify", "open", "run", "restart", "resolve", "reset"))]
        if actionable:
            raw_answer = f"Based on corporate IT documentation [1]: {actionable[0]}"
            if len(actionable) > 1:
                raw_answer += f" Additionally, {actionable[1].lower()}"
        else:
            raw_answer = f"{top.excerpt} [1]"

    if not raw_answer or INSUFFICIENT_CONTEXT_TOKEN in raw_answer:
        return None, True, hits, 0.0

    # Sanitize citation markers so only indices referring to actual retrieved hits are retained
    valid_indices = set(range(1, len(hits) + 1))
    cited_indices: set[int] = set()

    def _filter_marker(match: re.Match) -> str:
        idx = int(match.group(1))
        if idx in valid_indices:
            cited_indices.add(idx)
            return match.group(0)
        return ""

    sanitized_answer = re.sub(r"\[(\d+)\]", _filter_marker, raw_answer).strip()
    sanitized_answer = re.sub(r" +", " ", sanitized_answer).strip()

    updated_hits: list[SearchHit] = []
    for idx, hit in enumerate(hits, start=1):
        is_cited = idx in cited_indices
        updated_hits.append(
            SearchHit(
                article_id=hit.article_id,
                title=hit.title,
                category=hit.category,
                chunk_id=hit.chunk_id,
                chunk_index=hit.chunk_index,
                score=hit.score,
                excerpt=hit.excerpt,
                cited=is_cited,
                text=hit.text,
            )
        )

    # Compute grounding score
    context_chunks = [h.text for h in hits]
    grounding_score = compute_grounding_score(sanitized_answer, context_chunks)

    return sanitized_answer, False, updated_hits, grounding_score
