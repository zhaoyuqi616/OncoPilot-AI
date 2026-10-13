from __future__ import annotations

from oncopilot_ai.agents.base import BaseAgent
from oncopilot_ai.retrieval.retriever import retrieve
from oncopilot_ai.security import AuthContext
from oncopilot_ai.tracing import append_event, timed_event


class LiteratureAgent(BaseAgent):
    name = "literature_agent"

    def run(self, state: dict) -> dict:
        with timed_event(state, self.name):
            auth_data = state["auth_context"]
            auth = AuthContext(
                user_id=auth_data["user_id"],
                workspace_id=auth_data["workspace_id"],
                roles=frozenset(auth_data.get("roles", [])),
                scopes=frozenset(auth_data.get("scopes", [])),
            )
            chunks = retrieve(state["question"], auth=auth, top_k=state.get("top_k"), filters=state.get("filters"))
            state["retrieved_chunks"] = chunks
            append_event(
                state,
                self.name,
                "success",
                {
                    "num_chunks": len(chunks),
                    "workspace_id": auth.workspace_id,
                    "filters": state.get("filters", {}),
                },
            )
            return state
