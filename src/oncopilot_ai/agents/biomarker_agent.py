from __future__ import annotations

from oncopilot_ai.agents.base import BaseAgent
from oncopilot_ai.llm.parsers import heuristic_extract_entities
from oncopilot_ai.tracing import append_event, timed_event


class BiomarkerAgent(BaseAgent):
    name = "biomarker_agent"

    def run(self, state: dict) -> dict:
        with timed_event(state, self.name):
            entities = heuristic_extract_entities(state.get("retrieved_chunks", []))
            state["extracted_entities"] = entities
            append_event(
                state,
                self.name,
                "success",
                {
                    "genes": entities.genes,
                    "variants": entities.variants,
                    "therapies": entities.therapies,
                    "mechanisms": entities.mechanisms,
                },
            )
            return state
