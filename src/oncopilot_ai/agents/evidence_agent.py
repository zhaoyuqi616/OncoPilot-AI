from __future__ import annotations

from oncopilot_ai.agents.trust_agent import TrustAgent


class EvidenceAgent(TrustAgent):
    """Backward-compatible alias. The production workflow uses TrustAgent directly."""
    name = "evidence_agent"
