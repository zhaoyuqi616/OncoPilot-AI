from __future__ import annotations


def make_chunk_id(doc_id: str, chunk_index: int) -> str:
    return f"{doc_id}_CHUNK_{chunk_index}"
