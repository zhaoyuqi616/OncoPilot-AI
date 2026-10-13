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
    return findings or ["No authorized, sufficiently reliable evidence was found in the current workspace corpus."]


def _confidence_phrase(confidence: str) -> str:
    return {
        "high": "Evidence is relatively strong within the authorized corpus, with expert review still required.",
        "moderate": "Evidence is directionally useful but should be checked against source documents and clinical context.",
        "low": "Evidence is limited; use only for literature triage or hypothesis generation.",
        "insufficient": "Evidence is insufficient in the authorized indexed corpus.",
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
            allow_external = bool(state.get("external_llm_allowed", False))

            client = get_client() if allow_external else None
            if client is not None and chunks:
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
                mode = "privacy-preserving fallback" if not allow_external else "local fallback"
                executive_summary = (
                    f"Based on the authorized local evidence, the answer centers on {mechanisms}. "
                    f"Overall confidence is {confidence} with an aggregate trust score of {trust_score:.2f}. "
                    f"This response used {mode} mode without transmitting source text to an external LLM."
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
                    safety_note=state.get("safety_note", "Human review is required."),
                ),
                evidence=evidence_summary,
                confidence=confidence,
                recommended_next_steps=[
                    "Open and review the highest-trust authorized source passages before scientific or clinical use.",
                    "Escalate patient-specific diagnosis/treatment decisions to qualified clinicians and institutional workflows.",
                    "Add validated metadata such as PubMed ID, study design, sample size, trial phase, and guideline version where available.",
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
            state["structured_answer"] = structured
            state["final_answer"] = (
                f"{structured.executive_summary}\n\n"
                f"Confidence: {structured.confidence} | Aggregate trust score: {trust_score:.2f}\n\n"
                "Key findings:\n- " + "\n- ".join(structured.key_findings[:5]) + "\n\n"
                f"Safety note: {structured.clinical_interpretation.safety_note}"
            )
            append_event(
                state,
                self.name,
                "success",
                {"confidence": confidence, "external_llm_used": client is not None, "num_citations": len(structured.citations)},
            )
            return state
