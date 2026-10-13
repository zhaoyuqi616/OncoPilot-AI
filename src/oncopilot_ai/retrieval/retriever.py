from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import faiss
import numpy as np

from oncopilot_ai.config import settings
from oncopilot_ai.ingestion.embedder import get_embedder
from oncopilot_ai.ingestion.index_builder import workspace_paths
from oncopilot_ai.logging_utils import get_logger
from oncopilot_ai.retrieval.filters import apply_filters
from oncopilot_ai.retrieval.reranker import rerank
from oncopilot_ai.security import AuthContext, can_access_chunk
from oncopilot_ai.utils.io import read_json

logger = get_logger(__name__)


@lru_cache(maxsize=16)
def load_index(workspace_id: str):
    index_path, _, _ = workspace_paths(workspace_id)
    if not Path(index_path).exists():
        raise FileNotFoundError(f"No index for workspace '{workspace_id}'")
    return faiss.read_index(str(index_path))


@lru_cache(maxsize=16)
def load_chunk_records(workspace_id: str) -> list[dict]:
    _, metadata_path, _ = workspace_paths(workspace_id)
    return read_json(metadata_path)


def clear_retrieval_cache() -> None:
    load_index.cache_clear()
    load_chunk_records.cache_clear()


def retrieve(
    question: str,
    auth: AuthContext,
    top_k: int | None = None,
    filters: dict | None = None,
) -> list[dict]:
    k = min(top_k or settings.default_top_k, settings.max_top_k)
    index = load_index(auth.workspace_id)
    metadata = load_chunk_records(auth.workspace_id)
    embedder = get_embedder()

    query_vec = embedder.encode([question], convert_to_numpy=True, normalize_embeddings=True)
    query_vec = np.asarray(query_vec, dtype="float32").reshape(1, -1)

    # Workspace is physically namespaced. Overfetch then apply document ACL before agents/LLM.
    search_k = min(index.ntotal, max(k * 10, 50))
    scores, indices = index.search(query_vec, search_k)
    chunks: list[dict] = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0:
            continue
        item = metadata[idx].copy()
        if not can_access_chunk(item, auth):
            continue
        item["score"] = float(score)
        chunks.append(item)
        if len(chunks) >= max(k * 4, k):
            break

    chunks = apply_filters(chunks, filters)
    chunks = rerank(chunks, question)[:k]
    logger.info("retrieval workspace=%s user_hash=%s chunks=%s", auth.workspace_id, __import__("hashlib").sha256(auth.user_id.encode()).hexdigest()[:10], len(chunks))
    return chunks
