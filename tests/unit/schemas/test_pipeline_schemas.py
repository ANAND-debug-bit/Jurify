from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.case import CaseProfile, PartyInfo
from app.schemas.document import DocumentType, GeneratedDocument
from app.schemas.evidence import EvidenceGap, EvidenceItem, EvidenceQuality, EvidenceReport
from app.schemas.judge import JudgeOpinion
from app.schemas.lawyer import LawyerMatch, LawyerProfile
from app.schemas.legal_research import LegalCitation, LegalProvision, LegalResearchResult
from app.schemas.risk import RiskAssessment
from app.schemas.strategy import ForumType, StrategyOption, StrategyPlan
from app.schemas.timeline import Timeline, TimelineEvent


# --- CaseProfile ---------------------------------------------------------


def test_case_profile_requires_confidence_between_0_and_1() -> None:
    with pytest.raises(ValidationError):
        CaseProfile(incident_category="consumer_dispute", summary="x", confidence=1.5)


def test_case_profile_defaults_are_empty_collections() -> None:
    profile = CaseProfile(incident_category="consumer_dispute", summary="x", confidence=0.5)
    assert profile.parties == []
    assert profile.facts_collected == {}
    assert profile.missing_fields == []


def test_case_profile_rejects_unknown_field() -> None:
    with pytest.raises(ValidationError):
        CaseProfile(
            incident_category="consumer_dispute",
            summary="x",
            confidence=0.5,
            not_a_real_field="oops",  # type: ignore[call-arg]
        )


def test_party_info_role_is_free_text_not_enum() -> None:
    party = PartyInfo(role="complainant", name="A")
    assert party.relationship_to_user is None


# --- Timeline --------------------------------------------------------------


def test_timeline_event_defaults() -> None:
    event = TimelineEvent(description="incident occurred", sequence_order=1)
    assert event.is_inconsistent is False
    assert event.supporting_evidence_refs == []


def test_timeline_requires_events_list() -> None:
    with pytest.raises(ValidationError):
        Timeline(inconsistencies=[], reconstructed_summary="x")  # type: ignore[call-arg]


# --- Legal research ----------------------------------------------------------


def test_legal_research_result_defaults_jurisdiction_to_india() -> None:
    provision = LegalProvision(
        title="x",
        plain_explanation="y",
        citations=[LegalCitation(act_name="BNS", section="103")],
    )
    result = LegalResearchResult(applicable_laws=[provision], overall_summary="s")
    assert result.jurisdiction == "India"


# --- Evidence ----------------------------------------------------------------


def test_evidence_quality_enum_rejects_unknown_value() -> None:
    with pytest.raises(ValidationError):
        EvidenceItem(evidence_type="photo", description="x", quality="excellent")


def test_evidence_report_completeness_score_bounded_0_to_100() -> None:
    item = EvidenceItem(evidence_type="photo", description="x", quality=EvidenceQuality.STRONG)
    with pytest.raises(ValidationError):
        EvidenceReport(
            submitted_evidence=[item],
            gaps=[],
            completeness_score=150.0,
            summary="s",
        )


def test_evidence_gap_priority_uses_urgency_level() -> None:
    gap = EvidenceGap(description="missing receipt", suggested_evidence="purchase receipt", priority="critical")
    assert gap.priority.value == "critical"


# --- Risk ----------------------------------------------------------------------


def test_risk_assessment_rejects_out_of_range_scores() -> None:
    with pytest.raises(ValidationError):
        RiskAssessment(
            financial_risk=-1.0,
            criminal_risk=10.0,
            urgency="low",
            needs_police=False,
            needs_lawyer=False,
            needs_medical=False,
            settlement_probability=50.0,
            case_strength=50.0,
            rationale="x",
        )


def test_risk_assessment_valid_construction() -> None:
    risk = RiskAssessment(
        financial_risk=10.0,
        criminal_risk=5.0,
        urgency="medium",
        needs_police=False,
        needs_lawyer=True,
        needs_medical=False,
        settlement_probability=60.0,
        case_strength=70.0,
        rationale="x",
    )
    assert risk.urgency.value == "medium"


# --- Strategy --------------------------------------------------------------------


def test_strategy_plan_recommended_index_and_forum_enum() -> None:
    option = StrategyOption(
        forum=ForumType.CONSUMER_COURT,
        description="File in consumer court",
        estimated_cost_inr=5000.0,
        estimated_time="2-4 weeks",
        difficulty="medium",
        success_probability=70.0,
    )
    plan = StrategyPlan(options=[option], recommended_option_index=0, reasoning="best fit")
    assert plan.options[0].forum == ForumType.CONSUMER_COURT
    assert plan.options[0].required_specialization is None


def test_forum_type_rejects_unknown_forum() -> None:
    with pytest.raises(ValidationError):
        StrategyOption(
            forum="small_claims_tribunal",
            description="x",
            estimated_cost_inr=0.0,
            estimated_time="x",
            difficulty="low",
            success_probability=50.0,
        )


# --- Document --------------------------------------------------------------------


def test_generated_document_requires_known_document_type() -> None:
    doc = GeneratedDocument(
        document_type=DocumentType.LEGAL_NOTICE, title="Notice", content="Dear Sir/Madam..."
    )
    assert doc.recipient is None


# --- Lawyer ----------------------------------------------------------------------


def test_lawyer_profile_rating_bounded_0_to_5() -> None:
    with pytest.raises(ValidationError):
        LawyerProfile(
            id="123e4567-e89b-12d3-a456-426614174000",
            full_name="Adv. Test",
            specialization="consumer",
            city="Delhi",
            languages=["en", "hi"],
            fee_range_inr=(1000.0, 5000.0),
            rating=5.5,
            years_experience=10,
        )


def test_lawyer_match_valid_construction() -> None:
    profile = LawyerProfile(
        id="123e4567-e89b-12d3-a456-426614174000",
        full_name="Adv. Test",
        specialization="consumer",
        city="Delhi",
        languages=["en", "hi"],
        fee_range_inr=(1000.0, 5000.0),
        rating=4.5,
        years_experience=10,
    )
    match = LawyerMatch(lawyer=profile, match_score=90.0, match_reason="specialization match")
    assert match.lawyer.city == "Delhi"


# --- Judge -----------------------------------------------------------------------


def test_judge_opinion_overall_rating_bounded() -> None:
    with pytest.raises(ValidationError):
        JudgeOpinion(
            strengths=["strong evidence"],
            weaknesses=["weak timeline"],
            likely_outcome="favorable",
            settlement_recommendation="settle",
            recommended_improvements=["gather receipts"],
            overall_case_rating=101.0,
        )
