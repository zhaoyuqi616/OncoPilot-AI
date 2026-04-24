from __future__ import annotations

from oncopilot_ai.config import settings
from oncopilot_ai.utils.ids import make_chunk_id
from oncopilot_ai.utils.text import chunk_text


def build_chunk_records(documents: list[dict[str, str]]) -> list[dict]:
    chunk_records: list[dict] = []
    for doc in documents:
        chunks = chunk_text(
            doc["text"],
            chunk_size_words=settings.chunk_size_words,
            overlap_words=settings.chunk_overlap_words,
        )
        for i, chunk in enumerate(chunks):
            chunk_records.append(
                {
                    "chunk_id": make_chunk_id(doc["doc_id"], i),
                    "doc_id": doc["doc_id"],
                    "title": doc["title"],
                    "chunk_index": i,
                    "text": chunk,
                }
            )
    return chunk_records
