from __future__ import annotations

from oncopilot_ai.agents.base import BaseAgent
from oncopilot_ai.safety import question_risk_flags, safety_note
from oncopilot_ai.security import external_llm_allowed
from oncopilot_ai.tracing import append_event, timed_event


class SafetyAgent(BaseAgent):
    name = "safety_agent"

    def run(self, state: dict) -> dict:
        with timed_event(state, self.name):
            chunks = state.get("retrieved_chunks", [])
            suspicious = [c for c in chunks if c.get("prompt_injection_suspected")]
            if suspicious:
                state["retrieved_chunks"] = [c for c in chunks if not c.get("prompt_injection_suspected")]
                state.setdefault("warnings", []).append(
                    f"Excluded {len(suspicious)} retrieved chunk(s) flagged for possible prompt injection."
                )
            flags = question_risk_flags(state.get("question", ""))
            state["risk_flags"] = flags
            state["safety_note"] = safety_note(flags)
            state["external_llm_allowed"] = external_llm_allowed(state.get("retrieved_chunks", []))
            if not state["external_llm_allowed"]:
                state.setdefault("warnings", []).append(
                    "Sensitive/restricted evidence detected; external LLM transmission is disabled by policy."
                )
            append_event(
                state,
                self.name,
                "success",
                {
                    "prompt_injection_chunks_removed": len(suspicious),
                    "risk_flags": flags,
                    "external_llm_allowed": state["external_llm_allowed"],
                },
            )
            return state
