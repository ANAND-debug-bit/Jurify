"""Shared base model and enums used across every schema module
(docs/architecture/08-pydantic-schemas.md §8)."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class NyayaBaseModel(BaseModel):
    """Base for every agent/API schema. extra="forbid" makes an agent
    hallucinating an extra field a validation failure rather than
    silently accepted data — this is what triggers BaseAgent's
    retry-with-error-feedback loop (§8.18, ADR-3)."""

    model_config = ConfigDict(extra="forbid", frozen=False, str_strip_whitespace=True)


class CaseStatus(StrEnum):
    """v2 list per docs/architecture/03-langgraph-workflow.md §3.2 — that
    doc's revision superseded the shorter v1 list originally shown in
    08-pydantic-schemas.md §8's code block; this is the reconciled,
    authoritative set."""

    INTAKE_IN_PROGRESS = "intake_in_progress"
    INTAKE_COMPLETE = "intake_complete"
    EMERGENCY_DETECTED = "emergency_detected"
    EMERGENCY_HANDLING = "emergency_handling"
    RECONSTRUCTING = "reconstructing"
    RESEARCHING = "researching"
    VERIFYING_CITATIONS = "verifying_citations"
    ANALYZING_EVIDENCE = "analyzing_evidence"
    AWAITING_EVIDENCE_UPLOAD = "awaiting_evidence_upload"
    ASSESSING_RISK = "assessing_risk"
    PLANNING_STRATEGY = "planning_strategy"
    CHECKING_GOV_SCHEMES = "checking_gov_schemes"
    GENERATING_DOCUMENTS = "generating_documents"
    MATCHING_LAWYERS = "matching_lawyers"
    EXPLAINING = "explaining"
    COMPLETE = "complete"
    SIMULATING_OPPOSITION = "simulating_opposition"
    JUDGED = "judged"
    FAILED = "failed"


class UrgencyLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
