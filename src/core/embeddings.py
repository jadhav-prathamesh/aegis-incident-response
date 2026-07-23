"""Embedding helpers for knowledge-base and similarity search."""

from __future__ import annotations

import hashlib
import math
import re
from functools import lru_cache

from openai import AsyncOpenAI

from src.core.config import get_settings
from src.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9_./:-]+")


class EmbeddingService:
    """Create embeddings with a provider when available and deterministic local fallback."""

    def __init__(self, dimension: int | None = None):
        self.dimension = dimension or settings.vector_db.embedding_dimension

    async def embed_text(self, text: str) -> list[float]:
        """Embed one text value."""
        vectors = await self.embed_texts([text])
        return vectors[0]

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed text values using configured provider or local hashing fallback."""
        if settings.llm.api_key:
            try:
                client = AsyncOpenAI(api_key=settings.llm.api_key, base_url=settings.llm.base_url)
                response = await client.embeddings.create(
                    model=settings.vector_db.embedding_model,
                    input=texts,
                )
                return [item.embedding for item in response.data]
            except Exception as exc:
                logger.warning("Embedding provider failed; using local fallback", error=str(exc))

        return [self._local_embedding(text) for text in texts]

    def _local_embedding(self, text: str) -> list[float]:
        """Create a stable hashed bag-of-tokens embedding for offline development."""
        vector = [0.0] * self.dimension
        for token in TOKEN_PATTERN.findall(text.lower()):
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimension
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    """Return cosine similarity for two vectors."""
    if not left or not right:
        return 0.0
    size = min(len(left), len(right))
    dot = sum(left[index] * right[index] for index in range(size))
    left_norm = math.sqrt(sum(value * value for value in left[:size]))
    right_norm = math.sqrt(sum(value * value for value in right[:size]))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


@lru_cache(maxsize=1)
def get_embedding_service() -> EmbeddingService:
    """Return cached embedding service."""
    return EmbeddingService()
