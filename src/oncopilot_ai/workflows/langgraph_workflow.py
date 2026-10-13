from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from oncopilot_ai.agents.biomarker_agent import BiomarkerAgent
from oncopilot_ai.agents.coordinator_agent import CoordinatorAgent
from oncopilot_ai.agents.literature_agent import LiteratureAgent
from oncopilot_ai.agents.safety_agent import SafetyAgent
from oncopilot_ai.agents.synthesis_agent import SynthesisAgent
from oncopilot_ai.agents.translation_agent import TranslationAgent
from oncopilot_ai.agents.trust_agent import TrustAgent
from oncopilot_ai.schemas import AskRequest, AskResponse, SourceItem
from oncopilot_ai.security import AuthContext
from oncopilot_ai.tracing import new_trace_id, save_trace


class OncologyGraphState(TypedDict, total=False):
    trace_id: str
    question: str
    top_k: int | None
    filters: dict[str, str]
    min_trust_score: float
    include_low_confidence: bool
    auth_context: dict[str, Any]
    task_type: str | None
    execution_plan: list[str]
    retrieved_chunks: list[dict[str, Any]]
    evidence_summary: list[Any]
    extracted_entities: Any
    translation_notes: str
    structured_answer: Any
    final_answer: str
    trust_score: float
    confidence: str
    external_llm_allowed: bool
    risk_flags: list[str]
    safety_note: str
    events: list[Any]
    warnings: list[str]
    errors: list[str]


def initialize_state(request: AskRequest, auth: AuthContext | None = None) -> OncologyGraphState:
    auth = auth or AuthContext(user_id="local-user", workspace_id="default", roles=frozenset({"researcher"}))
    filters = {}
    if request.disease:
        filters["disease"] = request.disease
    if request.gene:
        filters["gene"] = request.gene
    return {
        "trace_id": new_trace_id(),
        "question": request.question,
        "top_k": request.top_k,
        "filters": filters,
        "min_trust_score": request.min_trust_score,
        "include_low_confidence": request.include_low_confidence,
        "auth_context": {
            "user_id": auth.user_id,
            "workspace_id": auth.workspace_id,
            "roles": sorted(auth.roles),
            "scopes": sorted(auth.scopes),
        },
        "task_type": None,
        "execution_plan": [],
        "retrieved_chunks": [],
        "evidence_summary": [],
        "extracted_entities": None,
        "translation_notes": "",
        "structured_answer": None,
        "final_answer": "",
        "trust_score": 0.0,
        "confidence": "insufficient",
        "external_llm_allowed": False,
        "risk_flags": [],
        "safety_note": "",
        "events": [],
        "warnings": [],
        "errors": [],
    }


def _node(agent):
    def run(state: OncologyGraphState) -> OncologyGraphState:
        return agent.run(dict(state))
    return run


def _route_after_trust(state: OncologyGraphState) -> str:
    if state.get("confidence") == "insufficient" and not state.get("include_low_confidence", False):
        return "synthesis_agent"
    return "biomarker_agent"


def build_oncology_graph():
    builder = StateGraph(OncologyGraphState)
    builder.add_node("coordinator_agent", _node(CoordinatorAgent()))
    builder.add_node("literature_agent", _node(LiteratureAgent()))
    builder.add_node("safety_agent", _node(SafetyAgent()))
    builder.add_node("trust_agent", _node(TrustAgent()))
    builder.add_node("biomarker_agent", _node(BiomarkerAgent()))
    builder.add_node("translation_agent", _node(TranslationAgent()))
    builder.add_node("synthesis_agent", _node(SynthesisAgent()))

    builder.add_edge(START, "coordinator_agent")
    builder.add_edge("coordinator_agent", "literature_agent")
    builder.add_edge("literature_agent", "safety_agent")
    builder.add_edge("safety_agent", "trust_agent")
    builder.add_conditional_edges(
        "trust_agent",
        _route_after_trust,
        {"biomarker_agent": "biomarker_agent", "synthesis_agent": "synthesis_agent"},
    )
    builder.add_edge("biomarker_agent", "translation_agent")
    builder.add_edge("translation_agent", "synthesis_agent")
    builder.add_edge("synthesis_agent", END)
    return builder.compile()


_COMPILED_GRAPH = None


def get_graph():
    global _COMPILED_GRAPH
    if _COMPILED_GRAPH is None:
        _COMPILED_GRAPH = build_oncology_graph()
    return _COMPILED_GRAPH


def _sources_from_state(state: OncologyGraphState) -> list[SourceItem]:
    return [
        SourceItem(
            doc_id=chunk["doc_id"], title=chunk["title"], chunk_id=chunk["chunk_id"],
            similarity_score=round(float(chunk.get("score", 0.0)), 4),
            trust_score=round(float(chunk.get("trust_score", 0.0)), 4),
            evidence_level=chunk.get("evidence_level", "unknown"),
            study_type=chunk.get("study_type", "unknown"),
            key_sentence=chunk.get("key_sentence"),
        )
        for chunk in state.get("retrieved_chunks", [])
    ]


def run_langgraph_workflow(request: AskRequest, auth: AuthContext | None = None) -> AskResponse:
    state = initialize_state(request, auth=auth)
    try:
        final_state = get_graph().invoke(state, config={"configurable": {"thread_id": state["trace_id"]}})
    except Exception as exc:
        state.setdefault("errors", []).append(type(exc).__name__)
        save_trace(state)
        raise

    save_trace(final_state)
    sources = _sources_from_state(final_state)
    structured = final_state["structured_answer"]
    return AskResponse(
        question=final_state["question"], answer=final_state["final_answer"], structured_answer=structured,
        sources=sources, extracted_entities=final_state.get("extracted_entities"),
        evidence_summary=final_state.get("evidence_summary", []), trust_score=round(float(final_state.get("trust_score", 0.0)), 4),
        confidence=final_state.get("confidence", "insufficient"), trace_id=final_state["trace_id"],
        warnings=final_state.get("warnings", []), safety_flags=final_state.get("risk_flags", []),
    )
