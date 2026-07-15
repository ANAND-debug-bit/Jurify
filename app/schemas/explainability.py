"""Explainability Agent output contract (NEW, Change 3).
docs/architecture/08-pydantic-schemas.md §8.15."""

from __future__ import annotations

from pydantic import Field

from app.schemas._common import NyayaBaseModel


class ExplainabilityItem(NyayaBaseModel):
    conclusion: str  # e.g. "Recommended forum: Consumer Court"
    reasoning: str
    supporting_evidence_refs: list[str]  # references into EvidenceReport items
    supporting_legal_refs: list[str]  # references into VerifiedLegalResearchResult provisions
    confidence_score: float = Field(ge=0.0, le=100.0)
    missing_information: list[str] = Field(default_factory=list)


class ExplainabilityReport(NyayaBaseModel):
    items: list[ExplainabilityItem]
