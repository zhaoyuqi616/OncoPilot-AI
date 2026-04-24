from __future__ import annotations


def normalize_whitespace(text: str) -> str:
    return " ".join(text.split())


def chunk_text(text: str, chunk_size_words: int = 120, overlap_words: int = 30) -> list[str]:
    text = normalize_whitespace(text)
    words = text.split()
    if len(words) <= chunk_size_words:
        return [text]

    chunks: list[str] = []
    start = 0
    step = max(1, chunk_size_words - overlap_words)
    while start < len(words):
        end = start + chunk_size_words
        chunk_words = words[start:end]
        if not chunk_words:
            break
        chunks.append(" ".join(chunk_words))
        if end >= len(words):
            break
        start += step
    return chunks
