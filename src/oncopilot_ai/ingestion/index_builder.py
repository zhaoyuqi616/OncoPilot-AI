from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import faiss
import numpy as np

from oncopilot_ai.config import settings
from oncopilot_ai.ingestion.chunker import build_chunk_records
from oncopilot_ai.ingestion.embedder import get_embedder
from oncopilot_ai.ingestion.loader import load_documents_from_workspace
from oncopilot_ai.logging_utils import get_logger
from oncopilot_ai.utils.io import write_json

logger = get_logger(__name__)


def workspace_paths(workspace_id: str) -> tuple[Path, Path, Path]:
    root = Path(settings.workspace_artifact_root) / workspace_id
    return root / "faiss" / "oncology.index", root / "metadata" / "chunks.json", root / "manifest.json"


def build_and_save_index(
    workspace_id: str = "default",
    sensitivity: str = "internal",
    allowed_roles: list[str] | None = None,
    allowed_users: list[str] | None = None,
) -> dict:
    defaults = {
        "sensitivity": sensitivity,
        "allowed_roles": allowed_roles or [],
        "allowed_users": allowed_users or [],
    }
    docs, errors = load_documents_from_workspace(workspace_id, defaults=defaults)
    if not docs:
        raise ValueError(f"No ingestible documents found for workspace '{workspace_id}'")

    chunk_records = build_chunk_records(docs)
    texts = [record["text"] for record in chunk_records]
    embedder = get_embedder()
    embeddings = embedder.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
    vectors = np.asarray(embeddings, dtype="float32")

    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)

    index_path, metadata_path, manifest_path = workspace_paths(workspace_id)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(index_path))
    write_json(metadata_path, chunk_records)

    manifest = {
        "workspace_id": workspace_id,
        "built_at": datetime.now(timezone.utc).isoformat(),
        "document_sections": len(docs),
        "chunks": len(chunk_records),
        "embedding_model": settings.embedding_model_name,
        "errors": errors,
    }
    write_json(manifest_path, manifest)

    # Drop cached copies so the API can use the new index without restart.
    try:
        from oncopilot_ai.retrieval.retriever import clear_retrieval_cache
        clear_retrieval_cache()
    except Exception:
        pass

    logger.info("index_built workspace=%s docs=%s chunks=%s errors=%s", workspace_id, len(docs), len(chunk_records), len(errors))
    return manifest
