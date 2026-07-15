"""Supervisor Agent output contract (NEW, Change 1).
docs/architecture/08-pydantic-schemas.md §8.11."""

from __future__ import annotations

from enum import StrEnum

from app.schemas._common import NyayaBaseModel


class NodeName(StrEnum):
    CASE_INTAKE = "case_intake"
    CASE_RECONSTRUCTION = "case_reconstruction"
    LEGAL_RESEARCH = "legal_research"
    EVIDENCE_ANALYSIS = "evidence_analysis"
    AWAITING_EVIDENCE_UPLOAD = "awaiting_evidence_upload"
    RISK_ASSESSMENT = "risk_assessment"
    STRATEGY_PLANNING = "strategy_planning"
    GOVERNMENT_SCHEME_AGENT = "government_scheme_agent"
    LAWYER_RECOMMENDATION = "lawyer_recommendation"
    COMPLAINT_GENERATION = "complaint_generation"
    EXPLAINABILITY_AGENT = "explainability_agent"
    FINALIZE_DASHBOARD = "finalize_dashboard"


class RoutingDecision(NyayaBaseModel):
    """Deliberately has no field capable of carrying legal reasoning,
    evidence judgments, or free-form case commentary — `reason` is a
    short routing justification, not analysis. This is the schema-level
    enforcement of "the Supervisor should never perform legal reasoning
    itself" (Change 1)."""

    next_node: NodeName
    reason: str
    needs_user_input: bool = False
