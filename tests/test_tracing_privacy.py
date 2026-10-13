from oncopilot_ai.security import AuthContext
from oncopilot_ai.schemas import AskRequest
from oncopilot_ai.workflows.langgraph_workflow import initialize_state


def test_state_has_explicit_workspace_identity():
    auth = AuthContext(user_id="u1", workspace_id="w1", roles=frozenset({"researcher"}))
    state = initialize_state(AskRequest(question="EGFR resistance"), auth=auth)
    assert state["auth_context"]["workspace_id"] == "w1"
    assert state["external_llm_allowed"] is False
