from __future__ import annotations

from oncopilot_ai.agents.base import BaseAgent
from oncopilot_ai.tracing import append_event, timed_event


class CoordinatorAgent(BaseAgent):
    name = "coordinator_agent"

    def run(self, state: dict) -> dict:
        with timed_event(state, self.name):
            question = state["question"].lower()
            if "resistance" in question or "osimertinib" in question or "progression" in question:
                task_type = "resistance_mechanism"
            elif "mrd" in question or "ctdna" in question or "minimal residual" in question:
                task_type = "mrd_biomarker_evidence"
            elif "trial" in question or "therapy" in question or "treatment" in question:
                task_type = "therapy_evidence_summary"
            else:
                task_type = "oncology_literature_summary"

            state["task_type"] = task_type
            state["execution_plan"] = [
                "coordinator_agent",
                "literature_agent",
                "trust_agent",
                "biomarker_agent",
                "translation_agent",
                "synthesis_agent",
            ]
            append_event(state, self.name, "success", {"task_type": task_type, "execution_plan": state["execution_plan"]})
            return state
