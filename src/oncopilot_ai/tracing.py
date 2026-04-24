from __future__ import annotations

import json
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from oncopilot_ai.config import settings
from oncopilot_ai.schemas import TraceEvent, TraceResponse


def new_trace_id() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"trace_{timestamp}_{uuid4().hex[:6]}"


def append_event(state: dict, agent: str, status: str, summary: dict | None = None, latency_ms: float | None = None) -> None:
    state.setdefault("events", [])
    state["events"].append(TraceEvent(agent=agent, status=status, latency_ms=latency_ms, summary=summary or {}))


@contextmanager
def timed_event(state: dict, agent: str):
    start = time.perf_counter()
    try:
        yield
    except Exception as exc:
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        append_event(state, agent, "error", {"error": str(exc)}, latency_ms=latency_ms)
        raise


def save_trace(state: dict) -> None:
    trace_dir = Path(settings.trace_dir)
    trace_dir.mkdir(parents=True, exist_ok=True)
    payload = TraceResponse(
        trace_id=state["trace_id"],
        question=state["question"],
        task_type=state.get("task_type"),
        execution_plan=state.get("execution_plan", []),
        events=state.get("events", []),
        final_trust_score=state.get("trust_score"),
        final_confidence=state.get("confidence"),
        warnings=state.get("warnings", []),
        errors=state.get("errors", []),
    )
    output_path = trace_dir / f"{state['trace_id']}.json"
    output_path.write_text(payload.model_dump_json(indent=2), encoding="utf-8")


def load_trace(trace_id: str) -> TraceResponse:
    trace_path = Path(settings.trace_dir) / f"{trace_id}.json"
    data = json.loads(trace_path.read_text(encoding="utf-8"))
    return TraceResponse(**data)
