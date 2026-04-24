from __future__ import annotations

from oncopilot_ai.schemas import AskRequest, AskResponse
from oncopilot_ai.workflows.langgraph_workflow import run_langgraph_workflow


def run_oncology_workflow(request: AskRequest) -> AskResponse:
    """Primary workflow entrypoint. Uses LangGraph explicit multi-agent control."""
    return run_langgraph_workflow(request)
