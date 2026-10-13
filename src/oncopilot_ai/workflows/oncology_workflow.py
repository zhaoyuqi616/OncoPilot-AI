from __future__ import annotations

from oncopilot_ai.schemas import AskRequest, AskResponse
from oncopilot_ai.security import AuthContext
from oncopilot_ai.workflows.langgraph_workflow import run_langgraph_workflow


def run_oncology_workflow(request: AskRequest, auth: AuthContext | None = None) -> AskResponse:
    """Primary workflow entrypoint with explicit authorization context."""
    return run_langgraph_workflow(request, auth=auth)
