"""Persisted, submitted evidence item.

Distinct from app.schemas.evidence.EvidenceItem, which is the Evidence
Analysis Agent's *assessment* of evidence (quality-scored, no id/case_id)
— this is the raw submitted record repositories persist and list.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.evidence import EvidenceGap, EvidenceItem


class Evidence(BaseModel):
    model_config = ConfigDict(frozen=False, from_attributes=True)

    id: UUID
    case_id: UUID
    evidence_type: str
    description: str | None = None
    file_url: str | None = None
    quality_rating: str | None = None
    created_at: datetime


class EvidenceSubmission(BaseModel):
    """What a caller supplies to submit one evidence item — no id/case_id/
    created_at yet, and no quality_rating (that's the Evidence Analysis
    Agent's job, not the submitter's)."""

    model_config = ConfigDict(frozen=False, from_attributes=True)

    evidence_type: str
    description: str | None = None
    file_url: str | None = None


class EvidenceReport(BaseModel):
    """Persisted Evidence Analysis Agent output — versioned by created_at,
    same "latest row per case_id" convention as RiskScore/Strategy
    (Module 14, closing the gap EvidenceService's Module 8 docstring
    flagged: "The Evidence Analysis Agent's quality assessment... are
    Module 14's job")."""

    model_config = ConfigDict(frozen=False, from_attributes=True)

    id: UUID
    case_id: UUID
    submitted_evidence: list[EvidenceItem] = Field(default_factory=list)
    gaps: list[EvidenceGap] = Field(default_factory=list)
    completeness_score: float | None = None
    summary: str | None = None
    created_at: datetime
