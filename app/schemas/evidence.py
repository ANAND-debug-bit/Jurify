"""Evidence Analysis Agent output contract.
docs/architecture/08-pydantic-schemas.md §8.4."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from app.schemas._common import NyayaBaseModel, UrgencyLevel


class EvidenceQuality(StrEnum):
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"


class EvidenceItem(NyayaBaseModel):
    evidence_type: str  # "photo", "document", "witness_statement", "receipt"
    description: str
    quality: EvidenceQuality
    notes: str | None = None


class EvidenceGap(NyayaBaseModel):
    description: str
    suggested_evidence: str
    priority: UrgencyLevel


class EvidenceReport(NyayaBaseModel):
    submitted_evidence: list[EvidenceItem]
    gaps: list[EvidenceGap]
    completeness_score: float = Field(ge=0.0, le=100.0)
    summary: str
