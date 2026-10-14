"""
Sorim.AI — Lexical Grounding Evaluation  (ai/safety/grounding.py)

Evaluates whether sentences in an AI-generated answer are supported
by retrieved knowledge context.
"""

from __future__ import annotations

import re


def compute_grounding_score(answer: str, context_chunks: list[str]) -> float:
    """
    Computes fraction of answer sentences with lexical keyword support in context.
    Returns float in [0.0, 1.0].
    """
    if not answer or not context_chunks:
        return 0.0

    full_context = " ".join(context_chunks).lower()
    context_words = set(re.findall(r"\w{4,}", full_context))
    if not context_words:
        return 0.5

    # Split answer into sentences
    sentences = [s.strip() for s in re.split(r"[.!?]\s+", answer) if len(s.strip()) > 10]
    if not sentences:
        return 1.0

    supported_count = 0
    for sentence in sentences:
        words = set(re.findall(r"\w{4,}", sentence.lower()))
        if not words:
            supported_count += 1
            continue
        overlap = words & context_words
        if len(overlap) / len(words) >= 0.25:
            supported_count += 1

    return round(supported_count / len(sentences), 2)
