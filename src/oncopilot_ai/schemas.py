from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from oncopilot_ai.config import settings


class HealthResponse(BaseModel):
    status: str
    version: str = settings.app_version
    model: str
    embedding_model: str
    graph: str = "langgraph"


class ReadinessResponse(BaseModel):
    ready: bool
    checks: dict[str, bool]
    notes: list[str] = []


class AskRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=settings.max_question_chars, description="Biomedical/oncology question")
    top_k: int | None = Field(default=None, ge=1, le=settings.max_top_k)
    disease: str | None = Field(default=None, max_length=120)
    gene: str | None = Field(default=None, max_length=80)
    min_trust_score: float = Field(default=0.55, ge=0.0, le=1.0)
    include_low_confidence: bool = Field(default=False)


class SourceItem(BaseModel):
    doc_id: str
    title: str
    chunk_id: str
    similarity_score: float
    trust_score: float = 0.0
    evidence_level: str = "unknown"
    study_type: str = "unknown"
    key_sentence: str | None = None


class EvidenceAssessment(BaseModel):
    doc_id: str
    chunk_id: str
    study_type: str
    evidence_level: Literal["A", "B", "C", "D", "unknown"] = "unknown"
    evidence_strength: Literal["high", "moderate", "low", "insufficient"] = "insufficient"
    similarity_score: float
    recency_score: float = 0.5
    study_design_score: float = 0.5
    specificity_score: float = 0.5
    trust_score: float = Field(..., ge=0.0, le=1.0)
    rationale: str
    limitation: str | None = None


class ExtractedEntities(BaseModel):
    genes: list[str] = []
    variants: list[str] = []
    therapies: list[str] = []
    mechanisms: list[str] = []
    diseases: list[str] = []


class ClinicalInterpretation(BaseModel):
    clinical_relevance: str
    patient_context_needed: list[str] = []
    actionability: Literal["hypothesis_generating", "translational_research", "clinical_trial_context", "clinical_decision_support_prototype"] = "hypothesis_generating"
    safety_note: str = "Human review is required."


class StructuredAnswer(BaseModel):
    question: str
    executive_summary: str
    key_findings: list[str]
    biomarkers: list[str]
    variants: list[str]
    therapies: list[str]
    mechanisms: list[str]
    clinical_interpretation: ClinicalInterpretation
    evidence: list[EvidenceAssessment]
    confidence: Literal["high", "moderate", "low", "insufficient"]
    recommended_next_steps: list[str]
    citations: list[SourceItem]


class AskResponse(BaseModel):
    question: str
    answer: str
    structured_answer: StructuredAnswer
    sources: list[SourceItem]
    extracted_entities: ExtractedEntities | None = None
    evidence_summary: list[EvidenceAssessment]
    trust_score: float
    confidence: str
    trace_id: str
    warnings: list[str] = []
    safety_flags: list[str] = []


class TraceEvent(BaseModel):
    agent: str
    status: str
    latency_ms: float | None = None
    summary: dict[str, Any] = {}


class TraceResponse(BaseModel):
    trace_id: str
    workspace_id: str | None = None
    user_hash: str | None = None
    question: str | None = None
    question_hash: str | None = None
    task_type: str | None = None
    execution_plan: list[str] = []
    events: list[TraceEvent] = []
    final_trust_score: float | None = None
    final_confidence: str | None = None
    warnings: list[str] = []
    errors: list[str] = []
