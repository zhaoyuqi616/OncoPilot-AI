from __future__ import annotations

from oncopilot_ai.agents.base import BaseAgent
from oncopilot_ai.retrieval.retriever import retrieve
from oncopilot_ai.tracing import append_event, timed_event


class LiteratureAgent(BaseAgent):
    name = "literature_agent"

    def run(self, state: dict) -> dict:
        with timed_event(state, self.name):
            chunks = retrieve(state["question"], top_k=state.get("top_k"), filters=state.get("filters"))
            state["retrieved_chunks"] = chunks
            append_event(
                state,
                self.name,
                "success",
                {
                    "num_chunks": len(chunks),
                    "top_doc_id": chunks[0]["doc_id"] if chunks else None,
                    "filters": state.get("filters", {}),
                },
            )
            return state
