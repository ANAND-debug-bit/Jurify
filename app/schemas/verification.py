"""Verification Agent output contract (NEW, Change 2).
docs/architecture/08-pydantic-schemas.md §8.13.

`LegalProvision.citations` inside `verified_provisions` is guaranteed (by
construction — the Verification Agent builds this list, nothing upstream
writes to it directly) to contain only citations with
`status == VERIFIED`. Downstream consumers use `VerifiedLegalResearchResult`,
never the raw `LegalResearchResult` — this is the enforcement mechanism
behind "every law shown to the user must pass through this verification
step."
"""

from __future__ import annotations

from enum import StrEnum

from app.schemas._common import NyayaBaseModel
from app.schemas.legal_research import LegalCitation, LegalProvision


class VerificationStatus(StrEnum):
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    REJECTED = "rejected"


class CitationVerification(NyayaBaseModel):
    citation: LegalCitation
    status: VerificationStatus
    verification_notes: str


class VerifiedLegalResearchResult(NyayaBaseModel):
    jurisdiction: str
    verified_provisions: list[LegalProvision]  # citations here are VERIFIED only
    rejected_citations: list[CitationVerification]  # kept for audit, never shown as fact
    verification_summary: str
