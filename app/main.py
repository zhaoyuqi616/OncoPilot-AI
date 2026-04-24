from __future__ import annotations

from fastapi import FastAPI, HTTPException

from oncopilot_ai.config import settings
from oncopilot_ai.schemas import AskRequest, AskResponse, HealthResponse, TraceResponse
from oncopilot_ai.tracing import load_trace
from oncopilot_ai.workflows.langgraph_workflow import build_oncology_graph
from oncopilot_ai.workflows.oncology_workflow import run_oncology_workflow

app = FastAPI(title="OncoPilot-AI", version="0.2.0")


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        model=settings.openai_model,
        embedding_model=settings.embedding_model_name,
    )


@app.get("/ping")
def ping() -> dict[str, bool]:
    return {"ok": True}


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    try:
        return run_oncology_workflow(request)
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/trace/{trace_id}", response_model=TraceResponse)
def get_trace(trace_id: str) -> TraceResponse:
    try:
        return load_trace(trace_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Trace not found: {trace_id}") from exc


@app.get("/graph")
def graph_spec() -> dict:
    graph = build_oncology_graph().get_graph()
    return {"nodes": [str(n) for n in graph.nodes], "edges": [str(e) for e in graph.edges]}
