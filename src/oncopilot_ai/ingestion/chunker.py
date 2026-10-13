from __future__ import annotations

from typing import Any

from oncopilot_ai.config import settings
from oncopilot_ai.utils.ids import make_chunk_id
from oncopilot_ai.utils.text import chunk_text


def build_chunk_records(documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    chunk_records: list[dict[str, Any]] = []
    for doc in documents:
        chunks = chunk_text(
            doc["text"],
            chunk_size_words=settings.chunk_size_words,
            overlap_words=settings.chunk_overlap_words,
        )
        inherited = {k: v for k, v in doc.items() if k not in {"text"}}
        for i, chunk in enumerate(chunks):
            section = str(doc.get("section", "document"))
            chunk_records.append(
                {
                    **inherited,
                    "chunk_id": make_chunk_id(f"{doc['doc_id']}_{section}", i),
                    "chunk_index": i,
                    "text": chunk,
                }
            )
    return chunk_records
