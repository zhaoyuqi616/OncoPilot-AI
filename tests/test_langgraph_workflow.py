from oncopilot_ai.workflows.langgraph_workflow import initialize_state
from oncopilot_ai.schemas import AskRequest


def test_initialize_state_filters():
    state = initialize_state(AskRequest(question="EGFR resistance in NSCLC", disease="NSCLC", gene="EGFR"))
    assert state["filters"] == {"disease": "NSCLC", "gene": "EGFR"}
    assert state["execution_plan"] == []
    assert state["confidence"] == "insufficient"
