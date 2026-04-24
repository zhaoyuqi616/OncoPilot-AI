from __future__ import annotations

from functools import lru_cache

from sentence_transformers import SentenceTransformer

from oncopilot_ai.config import settings


@lru_cache(maxsize=1)
def get_embedder() -> SentenceTransformer:
    return SentenceTransformer(settings.embedding_model_name)
