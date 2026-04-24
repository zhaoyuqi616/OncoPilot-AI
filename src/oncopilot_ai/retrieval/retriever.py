from __future__ import annotations

from functools import lru_cache

import faiss
import numpy as np

from oncopilot_ai.config import settings
from oncopilot_ai.ingestion.embedder import get_embedder
from oncopilot_ai.logging_utils import get_logger
from oncopilot_ai.retrieval.filters import apply_filters
from oncopilot_ai.retrieval.reranker import rerank
from oncopilot_ai.utils.io import read_json

logger = get_logger(__name__)


@lru_cache(maxsize=1)
def load_index():
    return faiss.read_index(settings.faiss_index_path)


@lru_cache(maxsize=1)
def load_chunk_records() -> list[dict]:
    return read_json(settings.metadata_path)


def retrieve(question: str, top_k: int | None = None, filters: dict | None = None) -> list[dict]:
    k = top_k or settings.default_top_k
    index = load_index()
    metadata = load_chunk_records()
    embedder = get_embedder()

    query_vec = embedder.encode([question], convert_to_numpy=True, normalize_embeddings=True)
    query_vec = np.asarray(query_vec, dtype="float32").reshape(1, -1)

    scores, indices = index.search(query_vec, k)
    chunks: list[dict] = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0:
            continue
        item = metadata[idx].copy()
        item["score"] = float(score)
        chunks.append(item)

    chunks = apply_filters(chunks, filters)
    chunks = rerank(chunks, question)
    logger.info("Retrieved %s chunks for query", len(chunks))
    return chunks
