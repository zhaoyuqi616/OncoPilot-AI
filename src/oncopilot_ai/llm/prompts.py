from __future__ import annotations

import json


def build_synthesis_prompt(question: str, chunks: list[dict], entities: dict, evidence_summary: list[dict], translation_notes: str) -> str:
    compact_sources = [
        {
            "doc_id": c.get("doc_id"),
            "chunk_id": c.get("chunk_id"),
            "title": c.get("title"),
            "trust_score": c.get("trust_score"),
            "evidence_level": c.get("evidence_level"),
            "key_sentence": c.get("key_sentence"),
            "text": c.get("text", "")[:1200],
        }
        for c in chunks[:6]
    ]
    return f"""
You are OncoPilot-AI, a research-grade oncology literature copilot for academic researchers and clinicians.

Question:
{question}

Extracted entities:
{json.dumps(entities, indent=2)}

Evidence scoring summary:
{json.dumps(evidence_summary, indent=2)}

Clinical translation notes:
{translation_notes}

Retrieved source snippets:
{json.dumps(compact_sources, indent=2)}

Write a careful answer with:
1. concise executive summary,
2. 3-5 evidence-grounded findings,
3. biomarker/mechanism/therapy relevance,
4. limitations and what clinical context is still needed.

Rules:
- Do not invent citations or claims not supported by retrieved snippets.
- Explicitly state when evidence is weak or insufficient.
- This is not medical advice; frame as research/clinical decision support prototype.
""".strip()
