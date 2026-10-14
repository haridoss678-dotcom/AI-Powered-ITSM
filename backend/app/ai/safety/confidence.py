"""
Sorim.AI — Confidence Calculation  (ai/safety/confidence.py)

Heuristic, explainable confidence calculation per ARCHITECTURE.md §13.
Not a calibrated probability.
"""

from __future__ import annotations

from app.core.config import get_settings
from app.schemas.analysis import Confidence, ConfidenceComponents


def compute_confidence(
    *,
    classification_agreement: float | None = None,
    retrieval_top_score: float | None = None,
    grounding_score: float | None = None,
    custom_threshold: float | None = None,
) -> Confidence:
    settings = get_settings()
    threshold = custom_threshold if custom_threshold is not None else settings.confidence_threshold

    components = ConfidenceComponents(
        classification_agreement=classification_agreement,
        retrieval_top_score=retrieval_top_score,
        grounding_score=grounding_score,
    )

    valid_scores = [
        s for s in (classification_agreement, retrieval_top_score, grounding_score)
        if s is not None
    ]

    if valid_scores:
        avg_score = round(sum(valid_scores) / len(valid_scores), 2)
    else:
        avg_score = 0.5

    below_threshold = avg_score < threshold

    if avg_score >= threshold + 0.15:
        level = "high"
    elif avg_score >= threshold:
        level = "medium"
    else:
        level = "low"

    return Confidence(
        score=avg_score,
        level=level,
        threshold=threshold,
        below_threshold=below_threshold,
        method="heuristic_v1",
        components=components,
        note="Heuristic score, not a calibrated probability",
    )
