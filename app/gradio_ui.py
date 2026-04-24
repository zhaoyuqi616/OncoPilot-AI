from __future__ import annotations

import json
from pathlib import Path

import gradio as gr
import pandas as pd

from oncopilot_ai.ingestion.index_builder import build_and_save_index
from oncopilot_ai.schemas import AskRequest
from oncopilot_ai.workflows.oncology_workflow import run_oncology_workflow


def _evidence_df(response) -> pd.DataFrame:
    rows = []
    for e in response.evidence_summary:
        rows.append({
            "doc_id": e.doc_id,
            "chunk_id": e.chunk_id,
            "study_type": e.study_type,
            "level": e.evidence_level,
            "strength": e.evidence_strength,
            "similarity": e.similarity_score,
            "trust": e.trust_score,
            "rationale": e.rationale,
        })
    return pd.DataFrame(rows)


def _source_df(response) -> pd.DataFrame:
    rows = []
    for s in response.sources:
        rows.append({
            "doc_id": s.doc_id,
            "title": s.title,
            "chunk_id": s.chunk_id,
            "similarity": s.similarity_score,
            "trust": s.trust_score,
            "level": s.evidence_level,
            "key_sentence": s.key_sentence,
        })
    return pd.DataFrame(rows)


def ask_oncopilot(question: str, top_k: int, disease: str, gene: str, min_trust_score: float, include_low_confidence: bool):
    if not question.strip():
        return "Please enter a question.", {}, pd.DataFrame(), pd.DataFrame(), ""
    request = AskRequest(
        question=question.strip(),
        top_k=int(top_k),
        disease=disease.strip() or None,
        gene=gene.strip() or None,
        min_trust_score=float(min_trust_score),
        include_low_confidence=include_low_confidence,
    )
    response = run_oncology_workflow(request)
    structured = response.structured_answer.model_dump()
    trace_path = str(Path("artifacts/traces") / f"{response.trace_id}.json")
    return response.answer, structured, _evidence_df(response), _source_df(response), trace_path


def rebuild_index():
    build_and_save_index()
    return "Index rebuilt from data/sample_docs. Add your oncology TXT documents there and rerun this button."


def build_ui() -> gr.Blocks:
    with gr.Blocks(title="OncoPilot-AI") as demo:
        gr.Markdown("# OncoPilot-AI — LangGraph Multi-Agent Oncology RAG Copilot")
        gr.Markdown(
            "Research prototype for evidence-grounded oncology Q&A. Not for diagnosis or treatment decisions."
        )
        with gr.Row():
            question = gr.Textbox(
                label="Clinical / translational oncology question",
                value="What are common resistance mechanisms to EGFR inhibitors in NSCLC?",
                lines=3,
            )
        with gr.Row():
            top_k = gr.Slider(1, 10, value=4, step=1, label="Top-k retrieved chunks")
            min_trust = gr.Slider(0, 1, value=0.35, step=0.05, label="Minimum trust score")
            include_low = gr.Checkbox(value=True, label="Include low-confidence evidence")
        with gr.Row():
            disease = gr.Textbox(label="Optional disease filter", placeholder="NSCLC")
            gene = gr.Textbox(label="Optional gene/biomarker filter", placeholder="EGFR")
        with gr.Row():
            ask_btn = gr.Button("Ask OncoPilot", variant="primary")
            rebuild_btn = gr.Button("Rebuild FAISS index")
        answer = gr.Markdown(label="Answer")
        structured = gr.JSON(label="Structured output")
        evidence = gr.Dataframe(label="Clinical-grade trust layer / evidence table")
        sources = gr.Dataframe(label="Retrieved sources")
        trace = gr.Textbox(label="Trace file path")
        status = gr.Textbox(label="Index status")

        ask_btn.click(
            ask_oncopilot,
            inputs=[question, top_k, disease, gene, min_trust, include_low],
            outputs=[answer, structured, evidence, sources, trace],
        )
        rebuild_btn.click(rebuild_index, outputs=[status])
    return demo


if __name__ == "__main__":
    build_ui().launch()
