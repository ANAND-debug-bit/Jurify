"""Legal Research Agent output contract.
docs/architecture/08-pydantic-schemas.md §8.3."""

from __future__ import annotations

from pydantic import Field

from app.schemas._common import NyayaBaseModel


class LegalCitation(NyayaBaseModel):
    act_name: str  # "Bharatiya Nyaya Sanhita, 2023"
    section: str  # "Section 318"
    source_url: str | None = None
    excerpt: str | None = None


class LegalProvision(NyayaBaseModel):
    title: str
    plain_explanation: str  # non-legalese explanation for the user
    applicable_rights: list[str] = Field(default_factory=list)
    punishments: list[str] = Field(default_factory=list)
    relevant_authority: str | None = None  # e.g. "Local Police Station", "Consumer Forum"
    citations: list[LegalCitation]


class LegalResearchResult(NyayaBaseModel):
    jurisdiction: str = "India"
    applicable_laws: list[LegalProvision]
    overall_summary: str
