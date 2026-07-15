"""Government Scheme Agent output contract (NEW, Change 5).
docs/architecture/08-pydantic-schemas.md §8.14."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from app.schemas._common import NyayaBaseModel


class GovernmentScheme(StrEnum):
    FREE_LEGAL_AID = "free_legal_aid"
    GOVERNMENT_COMPENSATION = "government_compensation"
    AYUSHMAN_BHARAT = "ayushman_bharat"
    WIDOW_SCHEME = "widow_scheme"
    SENIOR_CITIZEN_SCHEME = "senior_citizen_scheme"
    LABOUR_WELFARE_SCHEME = "labour_welfare_scheme"
    WOMEN_PROTECTION_SCHEME = "women_protection_scheme"


class GovernmentSchemeMatch(NyayaBaseModel):
    scheme: GovernmentScheme
    eligible: bool
    confidence: float = Field(ge=0.0, le=100.0)
    documents_required: list[str]
    how_to_apply: str
    relevant_authority: str


class GovernmentSchemeReport(NyayaBaseModel):
    matches: list[GovernmentSchemeMatch]
