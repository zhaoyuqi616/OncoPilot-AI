from __future__ import annotations

from oncopilot_ai.agents.base import BaseAgent
from oncopilot_ai.tracing import append_event, timed_event


class TranslationAgent(BaseAgent):
    name = "translation_agent"

    def run(self, state: dict) -> dict:
        with timed_event(state, self.name):
            entities = state.get("extracted_entities")
            genes = ", ".join(entities.genes) if entities and entities.genes else "no dominant gene signal"
            mechanisms = ", ".join(entities.mechanisms) if entities and entities.mechanisms else "limited mechanistic detail"
            therapies = ", ".join(entities.therapies) if entities and entities.therapies else "no specific therapy extracted"
            note = (
                f"Translational interpretation: retrieved evidence highlights {genes}; "
                f"candidate mechanisms include {mechanisms}; therapy context includes {therapies}. "
                "Use this output to support hypothesis generation, literature triage, biomarker strategy, "
                "and tumor-board preparation, but not as standalone medical advice."
            )
            state["translation_notes"] = note
            append_event(state, self.name, "success", {"note_preview": note[:180]})
            return state
