from __future__ import annotations

import re


def question_risk_flags(question: str) -> list[str]:
    """Deterministic flags used to add human-review warnings, not medical diagnosis."""
    q = question.lower()
    flags: list[str] = []
    if re.search(r"\b(my patient|this patient|patient id|mrn|date of birth|dob)\b", q):
        flags.append("possible_patient_specific_context")
    if re.search(r"\b(what should (i|we) treat|prescribe|dose|diagnose|stop treatment|start treatment)\b", q):
        flags.append("high_stakes_clinical_action_request")
    return flags


def safety_note(flags: list[str]) -> str:
    if "high_stakes_clinical_action_request" in flags:
        return (
            "Patient-specific diagnosis or treatment actions require qualified clinical review. "
            "OncoPilot-AI can summarize the authorized evidence but must not be used as an autonomous decision maker."
        )
    if flags:
        return "Potential patient-specific context detected; apply institutional privacy and clinical-review procedures."
    return "Use as evidence-grounded research/clinical decision support with human review."
