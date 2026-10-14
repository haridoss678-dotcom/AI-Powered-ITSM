"""
Sorim.AI — Embedding Service  (ai/rag/embedding_service.py)

Manages sentence-transformers/all-MiniLM-L6-v2 embedding generation.
"""

from __future__ import annotations

import hashlib
import importlib.util
import math
import re
from typing import Any

from app.core.config import get_settings

EMBEDDING_DIM = 384


class EmbeddingService:
    def __init__(self) -> None:
        self._model: Any = None
        self._last_error: str | None = None
        self._is_mock_fallback: bool = False

    def is_available(self) -> bool:
        return importlib.util.find_spec("sentence_transformers") is not None

    def _ensure_model(self) -> None:
        if self._model is not None:
            return

        settings = get_settings()
        if not self.is_available():
            self._is_mock_fallback = True
            self._last_error = "sentence_transformers package is not installed."
            return

        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(settings.embedding_model_id)
            self._is_mock_fallback = False
            self._last_error = None
        except Exception as exc:
            self._model = None
            self._is_mock_fallback = True
            self._last_error = f"Failed to load embedding model: {exc}"

    def health_status(self) -> dict[str, Any]:
        settings = get_settings()
        installed = self.is_available()
        status = "not_configured"
        if installed:
            status = "error" if self._last_error else "ok"
        return {
            "status": status,
            "detail": self._last_error,
            "meta": {
                "model_id": settings.embedding_model_id,
                "dimension": EMBEDDING_DIM,
                "installed": installed,
                "loaded": self._model is not None,
            },
        }

    STOPWORDS = {
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

    def _deterministic_embedding(self, text: str) -> list[float]:
        """
        Deterministic, normalized 384-dimensional vector representation.
        Enables vector similarity search and RAG testing in environments
        where sentence-transformers has not yet been installed.
        """
        vec = [0.0] * EMBEDDING_DIM
        raw_tokens = re.findall(r"[a-z0-9_-]+", text.lower())
        tokens = [t for t in raw_tokens if t not in self.STOPWORDS and len(t) > 1]
        if not tokens:
            tokens = raw_tokens or ["empty"]

        for token in tokens:
            token_hash = int(hashlib.md5(token.encode("utf-8")).hexdigest()[:8], 16)
            idx = token_hash % EMBEDDING_DIM
            weight = math.log(1.0 + len(token))
            vec[idx] += weight

        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec

    def embed_text(self, text: str) -> list[float]:
        self._ensure_model()
        if self._model is not None:
            raw = self._model.encode(text, normalize_embeddings=True)
            return [float(x) for x in raw]
        return self._deterministic_embedding(text)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        self._ensure_model()
        if self._model is not None:
            raw = self._model.encode(texts, normalize_embeddings=True)
            return [[float(x) for x in vec] for vec in raw]
        return [self._deterministic_embedding(t) for t in texts]


_embedding_service = EmbeddingService()


def get_embedding_service() -> EmbeddingService:
    return _embedding_service
