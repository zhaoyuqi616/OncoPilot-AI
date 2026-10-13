from __future__ import annotations

import time
from collections import defaultdict, deque
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from oncopilot_ai.config import settings
from oncopilot_ai.ingestion.index_builder import workspace_paths
from oncopilot_ai.schemas import AskRequest, AskResponse, HealthResponse, ReadinessResponse, TraceResponse
from oncopilot_ai.security import AuthContext, get_current_user
from oncopilot_ai.tracing import load_trace
from oncopilot_ai.workflows.langgraph_workflow import build_oncology_graph
from oncopilot_ai.workflows.oncology_workflow import run_oncology_workflow

app = FastAPI(title="OncoPilot-AI", version=settings.app_version)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type", "X-User-ID", "X-Workspace-ID", "X-Roles", "X-Request-ID"],
)

_rate_windows: dict[str, deque[float]] = defaultdict(deque)


@app.middleware("http")
async def production_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or uuid4().hex
    now = time.time()
    client_key = request.client.host if request.client else "unknown"
    bucket = _rate_windows[client_key]
    while bucket and bucket[0] < now - 60:
        bucket.popleft()
    if len(bucket) >= settings.rate_limit_per_minute:
        return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded", "request_id": request_id})
    bucket.append(now)
    started = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Response-Time-Ms"] = str(round((time.perf_counter() - started) * 1000, 2))
    return response


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", model=settings.openai_model, embedding_model=settings.embedding_model_name)


@app.get("/ready", response_model=ReadinessResponse)
def ready(auth: AuthContext = Depends(get_current_user)) -> ReadinessResponse:
    index_path, metadata_path, _ = workspace_paths(auth.workspace_id)
    checks = {
        "workspace_index": index_path.exists() and metadata_path.exists(),
        "production_auth": settings.app_env != "production" or settings.auth_mode == "jwt",
        "production_cors": settings.app_env != "production" or "*" not in settings.origin_list,
        "trace_redaction": not settings.trace_store_question,
    }
    notes = []
    if settings.app_env == "production" and settings.auth_mode != "jwt":
        notes.append("Production requires AUTH_MODE=jwt.")
    if not checks["workspace_index"]:
        notes.append(f"No retrieval index is available for workspace '{auth.workspace_id}'.")
    return ReadinessResponse(ready=all(checks.values()), checks=checks, notes=notes)


@app.get("/ping")
def ping() -> dict[str, bool]:
    return {"ok": True}


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest, auth: AuthContext = Depends(get_current_user)) -> AskResponse:
    try:
        return run_oncology_workflow(request, auth=auth)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail="Workspace knowledge index is not ready") from exc
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail="Request failed; use the request/trace ID for support") from exc


@app.get("/trace/{trace_id}", response_model=TraceResponse)
def get_trace(trace_id: str, auth: AuthContext = Depends(get_current_user)) -> TraceResponse:
    try:
        trace = load_trace(trace_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Trace not found") from exc
    if trace.workspace_id != auth.workspace_id and not auth.is_admin:
        raise HTTPException(status_code=404, detail="Trace not found")
    return trace


@app.get("/graph")
def graph_spec(auth: AuthContext = Depends(get_current_user)) -> dict:
    if not auth.is_admin:
        raise HTTPException(status_code=403, detail="Admin role required")
    graph = build_oncology_graph().get_graph()
    return {"nodes": [str(n) for n in graph.nodes], "edges": [str(e) for e in graph.edges]}
