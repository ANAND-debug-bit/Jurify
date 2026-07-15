from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.emergency import (
    EmergencyAssessment,
    EmergencyCategory,
    EmergencyGuidance,
    HelplineInfo,
)
from app.schemas.explainability import ExplainabilityItem, ExplainabilityReport
from app.schemas.government_scheme import (
    GovernmentScheme,
    GovernmentSchemeMatch,
    GovernmentSchemeReport,
)
from app.schemas.legal_research import LegalCitation
from app.schemas.verification import (
    CitationVerification,
    VerificationStatus,
    VerifiedLegalResearchResult,
)


# --- Emergency (Change 4) ---------------------------------------------------


def test_emergency_category_includes_none_for_the_non_emergency_case() -> None:
    assessment = EmergencyAssessment(
        is_emergency=False, category=EmergencyCategory.NONE, severity="low", rationale="routine dispute"
    )
    assert assessment.category == EmergencyCategory.NONE


def test_emergency_category_rejects_unknown_category() -> None:
    with pytest.raises(ValidationError):
        EmergencyAssessment(is_emergency=True, category="fire", severity="critical", rationale="x")


def test_emergency_guidance_requires_all_four_lists() -> None:
    guidance = EmergencyGuidance(
        immediate_steps=["call police"],
        evidence_preservation_checklist=["photograph injuries"],
        helplines=[HelplineInfo(name="Women's Helpline", phone="181", available="24x7")],
        recommended_authorities=["Local Police Station"],
    )
    assert guidance.helplines[0].available == "24x7"


# --- Verification (Change 2) ------------------------------------------------


def test_citation_verification_embeds_the_original_citation() -> None:
    verification = CitationVerification(
        citation=LegalCitation(act_name="BNS", section="103"),
        status=VerificationStatus.REJECTED,
        verification_notes="section does not exist",
    )
    assert verification.citation.act_name == "BNS"
    assert verification.status == VerificationStatus.REJECTED


def test_verified_legal_research_result_separates_verified_from_rejected() -> None:
    result = VerifiedLegalResearchResult(
        jurisdiction="India",
        verified_provisions=[],
        rejected_citations=[
            CitationVerification(
                citation=LegalCitation(act_name="Fake Act", section="1"),
                status=VerificationStatus.REJECTED,
                verification_notes="hallucinated",
            )
        ],
        verification_summary="1 citation rejected",
    )
    assert len(result.verified_provisions) == 0
    assert len(result.rejected_citations) == 1


# --- Government Scheme (Change 5) -------------------------------------------


def test_government_scheme_match_confidence_bounded_0_to_100() -> None:
    with pytest.raises(ValidationError):
        GovernmentSchemeMatch(
            scheme=GovernmentScheme.FREE_LEGAL_AID,
            eligible=True,
            confidence=150.0,
            documents_required=["income certificate"],
            how_to_apply="Visit District Legal Services Authority",
            relevant_authority="DLSA",
        )


def test_government_scheme_report_holds_multiple_matches() -> None:
    match = GovernmentSchemeMatch(
        scheme=GovernmentScheme.AYUSHMAN_BHARAT,
        eligible=False,
        confidence=20.0,
        documents_required=[],
        how_to_apply="N/A",
        relevant_authority="N/A",
    )
    report = GovernmentSchemeReport(matches=[match])
    assert report.matches[0].scheme == GovernmentScheme.AYUSHMAN_BHARAT


# --- Explainability (Change 3) ----------------------------------------------


def test_explainability_item_missing_information_defaults_empty() -> None:
    item = ExplainabilityItem(
        conclusion="Recommended forum: Consumer Court",
        reasoning="Best fit for a consumer dispute under 20 lakh",
        supporting_evidence_refs=["evidence-1"],
        supporting_legal_refs=["provision-1"],
        confidence_score=85.0,
    )
    assert item.missing_information == []


def test_explainability_report_holds_multiple_items() -> None:
    item = ExplainabilityItem(
        conclusion="x",
        reasoning="y",
        supporting_evidence_refs=[],
        supporting_legal_refs=[],
        confidence_score=50.0,
    )
    report = ExplainabilityReport(items=[item, item])
    assert len(report.items) == 2
