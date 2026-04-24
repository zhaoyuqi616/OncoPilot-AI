from __future__ import annotations

import re
from statistics import mean

from oncopilot_ai.agents.base import BaseAgent
from oncopilot_ai.schemas import EvidenceAssessment
from oncopilot_ai.tracing import append_event, timed_event


def _study_type(text: str, title: str) -> tuple[str, float, str]:
    combined = f"{title} {text}".lower()
    if any(x in combined for x in ["randomized", "phase iii", "phase 3", "prospective trial"]):
        return "randomized/prospective clinical trial", 1.0, "A"
    if any(x in combined for x in ["clinical trial", "phase ii", "phase 2", "patients", "cohort"]):
        return "clinical/translational cohort", 0.8, "B"
    if any(x in combined for x in ["review", "meta-analysis", "guideline", "consensus"]):
        return "review/guideline", 0.7, "B"
    if any(x in combined for x in ["cell line", "xenograft", "mouse", "mechanism", "pathway"]):
        return "preclinical/mechanistic", 0.55, "C"
    return "literature snippet/unknown design", 0.4, "D"


def _specificity(question: str, text: str) -> float:
    q_terms = {t for t in re.findall(r"[a-zA-Z0-9]+", question.lower()) if len(t) > 3}
    if not q_terms:
        return 0.5
    text_l = text.lower()
    hits = sum(1 for t in q_terms if t in text_l)
    return min(1.0, hits / max(3, len(q_terms)))


def _recency(text: str) -> float:
    years = [int(y) for y in re.findall(r"\b(20[0-2][0-9]|19[8-9][0-9])\b", text)]
    if not years:
        return 0.5
    y = max(years)
    if y >= 2023:
        return 1.0
    if y >= 2019:
        return 0.8
    if y >= 2015:
        return 0.6
    return 0.4


def _strength(score: float) -> str:
    if score >= 0.78:
        return "high"
    if score >= 0.55:
        return "moderate"
    if score >= 0.35:
        return "low"
    return "insufficient"


def _key_sentence(text: str, question: str) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    q_terms = {t for t in re.findall(r"[a-zA-Z0-9]+", question.lower()) if len(t) > 3}
    if not sentences:
        return text[:240]
    ranked = sorted(sentences, key=lambda s: sum(t in s.lower() for t in q_terms), reverse=True)
    return ranked[0][:300]


class TrustAgent(BaseAgent):
    name = "trust_agent"

    def run(self, state: dict) -> dict:
        with timed_event(state, self.name):
            question = state["question"]
            assessments: list[EvidenceAssessment] = []
            trusted_chunks = []
            min_score = float(state.get("min_trust_score", 0.35))
            include_low = bool(state.get("include_low_confidence", True))

            for chunk in state.get("retrieved_chunks", []):
                text = chunk.get("text", "")
                title = chunk.get("title", "")
                study_type, study_design_score, level = _study_type(text, title)
                similarity = max(0.0, min(1.0, float(chunk.get("score", 0.0))))
                specificity = _specificity(question, f"{title} {text}")
                recency = _recency(text)
                trust_score = round(0.40 * similarity + 0.25 * specificity + 0.25 * study_design_score + 0.10 * recency, 3)
                strength = _strength(trust_score)
                chunk["trust_score"] = trust_score
                chunk["evidence_level"] = level
                chunk["study_type"] = study_type
                chunk["key_sentence"] = _key_sentence(text, question)
                assessment = EvidenceAssessment(
                    doc_id=chunk["doc_id"],
                    chunk_id=chunk["chunk_id"],
                    study_type=study_type,
                    evidence_level=level,
                    evidence_strength=strength, 
                    similarity_score=round(similarity, 3),
                    recency_score=round(recency, 3),
                    study_design_score=round(study_design_score, 3),
                    specificity_score=round(specificity, 3),
                    trust_score=trust_score,
                    rationale=f"Composite trust score uses retrieval similarity, question-specific term overlap, inferred study design, and recency.",
                    limitation="Heuristic research prototype; validate against manually curated evidence labels before clinical use.",
                )
                assessments.append(assessment)
                if include_low or trust_score >= min_score:
                    trusted_chunks.append(chunk)

            trusted_chunks = sorted(trusted_chunks, key=lambda c: c.get("trust_score", 0), reverse=True)
            state["retrieved_chunks"] = trusted_chunks
            state["evidence_summary"] = sorted(assessments, key=lambda x: x.trust_score, reverse=True)
            state["trust_score"] = round(mean([a.trust_score for a in assessments]), 3) if assessments else 0.0
            if state["trust_score"] >= 0.78:
                state["confidence"] = "high"
            elif state["trust_score"] >= 0.55:
                state["confidence"] = "moderate"
            elif state["trust_score"] >= 0.35:
                state["confidence"] = "low"
            else:
                state["confidence"] = "insufficient"
                state.setdefault("warnings", []).append("Evidence trust score is low; answer should be treated as hypothesis-generating only.")

            append_event(state, self.name, "success", {"num_evidence_items": len(assessments), "trust_score": state["trust_score"], "confidence": state["confidence"]})
            return state
