"""Persisted legal research result.

Not in the original 8-file domain/entities/ list — added here (Module 12)
because Legal Research needs a persistence path through CaseRepository,
same as timeline/risk/strategy/document/opposition/explainability.
`applicable_laws` reuses app.schemas.legal_research.LegalProvision
directly (like Lawyer reuses LawyerProfile) rather than a redundant
parallel type — the individual citations inside each provision are also
exploded into their own `legal_citations` rows by the repository, so the
Verification Agent (Module 13) can update per-citation verification
status independently.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.legal_research import LegalProvision


class LegalResearchResult(BaseModel):
    model_config = ConfigDict(frozen=False, from_attributes=True)

    id: UUID
    case_id: UUID
    jurisdiction: str
    applicable_laws: list[LegalProvision] = Field(default_factory=list)
    plain_explanation: str | None = None
    created_at: datetime


class LegalCitationRecord(BaseModel):
    """One exploded `legal_citations` row — the persistence unit the
    Verification Agent (Module 13) updates in place. Distinct from
    `app.schemas.legal_research.LegalCitation` (a plain value object with
    no identity or verification state) and from
    `app.schemas.verification.CitationVerification` (the agent's
    in-memory verdict before it's applied to a specific row)."""

    model_config = ConfigDict(frozen=False, from_attributes=True)

    id: UUID
    legal_research_result_id: UUID
    act_name: str
    section: str | None = None
    source_url: str | None = None
    excerpt: str | None = None
    is_verified: bool
    verification_status: str
    verification_notes: str | None = None
    verified_at: datetime | None = None
