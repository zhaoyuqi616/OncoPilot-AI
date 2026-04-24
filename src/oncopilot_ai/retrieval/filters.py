from __future__ import annotations


def apply_filters(chunks: list[dict], filters: dict | None = None) -> list[dict]:
    if not filters:
        return chunks
    filtered = chunks
    disease = filters.get("disease")
    gene = filters.get("gene")
    if disease:
        filtered = [c for c in filtered if disease.lower() in c["text"].lower() or disease.lower() in c["title"].lower()]
    if gene:
        filtered = [c for c in filtered if gene.lower() in c["text"].lower() or gene.lower() in c["title"].lower()]
    return filtered
