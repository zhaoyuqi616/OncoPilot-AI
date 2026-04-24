from __future__ import annotations

from oncopilot_ai.agents.base import BaseAgent
from oncopilot_ai.config import settings
from oncopilot_ai.llm.client import get_client
from oncopilot_ai.llm.prompts import build_synthesis_prompt
from oncopilot_ai.schemas import ClinicalInterpretation, StructuredAnswer
from oncopilot_ai.tracing import append_event, timed_event


def _fallback_key_findings(chunks: list[dict]) -> list[str]:
    findings = []
    for chunk in chunks[:4]:
        sentence = chunk.get("key_sentence") or chunk.get("text", "")[:220]
        findings.append(f"{sentence} [source: {chunk.get('doc_id')}, trust={chunk.get('trust_score', 0):.2f}]")
    return findings or ["No retrievable evidence was found in the current local knowledge base."]


def _confidence_phrase(confidence: str) -> str:
    return {
        "high": "Evidence appears relatively strong for a research prototype, but still requires expert review.",
        "moderate": "Evidence is directionally useful but should be checked against source documents and clinical context.",
        "low": "Evidence is limited; use only for hypothesis generation or literature triage.",
        "insufficient": "Evidence is insufficient in the indexed corpus.",
    }.get(confidence, "Evidence confidence is uncertain.")


class SynthesisAgent(BaseAgent):
    name = "synthesis_agent"

    def run(self, state: dict) -> dict:
        with timed_event(state, self.name):
            chunks = state.get("retrieved_chunks", [])
            entities = state.get("extracted_entities")
            evidence_summary = state.get("evidence_summary", [])
            translation_notes = state.get("translation_notes", "")
            confidence = state.get("confidence", "insufficient")
            trust_score = float(state.get("trust_score", 0.0))

            client = get_client()
            if client is not None:
                prompt = build_synthesis_prompt(
                    state["question"],
                    chunks,
                    entities.model_dump() if entities else {},
                    [item.model_dump() for item in evidence_summary],
                    translation_notes,
                )
                response = client.responses.create(model=settings.openai_model, input=prompt)
                executive_summary = response.output_text.strip()
            else:
                mechanisms = ", ".join(entities.mechanisms) if entities and entities.mechanisms else "limited clearly extracted mechanisms"
                executive_summary = (
                    f"Based on the local indexed evidence, the answer centers on {mechanisms}. "
                    f"Overall confidence is {confidence} with an aggregate trust score of {trust_score:.2f}. "
                    "This was generated in fallback mode without an external LLM."
                )

            if entities is None:
                from oncopilot_ai.schemas import ExtractedEntities
                entities = ExtractedEntities()

            structured = StructuredAnswer(
                question=state["question"],
                executive_summary=executive_summary,
                key_findings=_fallback_key_findings(chunks),
                biomarkers=entities.genes,
                variants=entities.variants,
                therapies=entities.therapies,
                mechanisms=entities.mechanisms,
                clinical_interpretation=ClinicalInterpretation(
                    clinical_relevance=translation_notes or _confidence_phrase(confidence),
                    patient_context_needed=[
                        "tumor type and stage",
                        "prior lines of therapy",
                        "assay type and sample source",
                        "variant allele fraction / expression cutoff where relevant",
                    ],
                    actionability="clinical_decision_support_prototype" if confidence in {"high", "moderate"} else "hypothesis_generating",
                ),
                evidence=evidence_summary,
                confidence=confidence,
                recommended_next_steps=[
                    "Review the highest-trust source chunks before using the output in a scientific or clinical discussion.",
                    "Add PubMed IDs, trial phase, sample size, and guideline tags to metadata for stronger evidence grading.",
                    "Validate answers against expert-curated examples before deploying to researchers or clinicians.",
                ],
                citations=[
                    {
                        "doc_id": chunk["doc_id"],
                        "title": chunk["title"],
                        "chunk_id": chunk["chunk_id"],
                        "similarity_score": round(float(chunk.get("score", 0.0)), 4),
                        "trust_score": round(float(chunk.get("trust_score", 0.0)), 4),
                        "evidence_level": chunk.get("evidence_level", "unknown"),
                        "study_type": chunk.get("study_type", "unknown"),
                        "key_sentence": chunk.get("key_sentence"),
                    }
                    for chunk in chunks
                ],
            )
            # Pydantic will coerce citation dicts into SourceItem.
            state["structured_answer"] = structured
            state["final_answer"] = (
                f"{structured.executive_summary}\n\n"
                f"Confidence: {structured.confidence} | Aggregate trust score: {trust_score:.2f}\n\n"
                "Key findings:\n- " + "\n- ".join(structured.key_findings[:5]) + "\n\n"
                f"Safety note: {structured.clinical_interpretation.safety_note}"
            )
            append_event(state, self.name, "success", {"answer_preview": state["final_answer"][:200], "confidence": confidence})
            return state
