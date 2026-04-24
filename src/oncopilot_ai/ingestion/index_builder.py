from __future__ import annotations

from pathlib import Path

import faiss
import numpy as np

from oncopilot_ai.config import settings
from oncopilot_ai.ingestion.chunker import build_chunk_records
from oncopilot_ai.ingestion.embedder import get_embedder
from oncopilot_ai.ingestion.loader import load_txt_documents_from_folder
from oncopilot_ai.logging_utils import get_logger
from oncopilot_ai.utils.io import write_json

logger = get_logger(__name__)


def build_and_save_index() -> None:
    docs = load_txt_documents_from_folder()
    logger.info("Loaded %s documents", len(docs))
    chunk_records = build_chunk_records(docs)
    logger.info("Built %s chunk records", len(chunk_records))

    texts = [record["text"] for record in chunk_records]
    embedder = get_embedder()
    embeddings = embedder.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
    vectors = np.asarray(embeddings, dtype="float32")

    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)

    index_path = Path(settings.faiss_index_path)
    metadata_path = Path(settings.metadata_path)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)

    faiss.write_index(index, str(index_path))
    write_json(metadata_path, chunk_records)

    logger.info("Saved FAISS index to %s", index_path)
    logger.info("Saved metadata to %s", metadata_path)
