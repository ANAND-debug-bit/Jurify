from __future__ import annotations

from uuid import uuid4

import pytest

from app.domain.exceptions import EntityNotFoundError
from app.schemas._common import CaseStatus
from app.schemas.case import CaseProfile
from app.schemas.document import DocumentType, GeneratedDocument
from app.schemas.language import SupportedLanguage
from app.schemas.risk import RiskAssessment
from app.schemas.strategy import ForumType, StrategyOption, StrategyPlan
from app.schemas.timeline import Timeline, TimelineEvent
from app.services.case_service import CaseService
from tests.unit.services.fakes import FakeCaseRepository, FakeEvidenceRepository


def _build_service() -> tuple[CaseService, FakeCaseRepository, FakeEvidenceRepository]:
    case_repo = FakeCaseRepository()
    evidence_repo = FakeEvidenceRepository()
    return CaseService(case_repo, evidence_repo), case_repo, evidence_repo


async def test_create_and_get_case() -> None:
    service, _, _ = _build_service()
    user_id = uuid4()

    case = await service.create_case(user_id, SupportedLanguage.HI)
    fetched = await service.get_case(case.id)

    assert fetched.user_id == user_id
    assert fetched.preferred_language == SupportedLanguage.HI
    assert fetched.status == CaseStatus.INTAKE_IN_PROGRESS


async def test_get_case_raises_when_missing() -> None:
    service, _, _ = _build_service()

    with pytest.raises(EntityNotFoundError):
        await service.get_case(uuid4())


async def test_list_cases_for_user() -> None:
    service, _, _ = _build_service()
    user_id = uuid4()
    other_user_id = uuid4()
    await service.create_case(user_id)
    await service.create_case(user_id)
    await service.create_case(other_user_id)

    cases = await service.list_cases_for_user(user_id)

    assert len(cases) == 2
    assert all(c.user_id == user_id for c in cases)


async def test_update_status_and_save_profile() -> None:
    service, _, _ = _build_service()
    case = await service.create_case(uuid4())

    await service.update_status(case.id, CaseStatus.RESEARCHING)
    profile = CaseProfile(incident_category="consumer_dispute", summary="x", confidence=0.7)
    await service.save_profile(case.id, profile)

    fetched = await service.get_case(case.id)
    assert fetched.status == CaseStatus.RESEARCHING
    assert fetched.case_profile is not None
    assert fetched.incident_category == "consumer_dispute"


async def test_stale_stages_empty_with_no_evidence() -> None:
    service, _, _ = _build_service()
    case = await service.create_case(uuid4())

    assert await service.get_stale_stages(case.id) == []


async def test_stale_stages_flags_risk_and_strategy_older_than_evidence() -> None:
    service, case_repo, evidence_repo = _build_service()
    case = await service.create_case(uuid4())

    await case_repo.add_risk_score(
        case.id,
        RiskAssessment(
            financial_risk=10.0, criminal_risk=5.0, urgency="low", needs_police=False,
            needs_lawyer=False, needs_medical=False, settlement_probability=50.0,
            case_strength=50.0, rationale="initial",
        ),
    )
    await case_repo.add_strategies(
        case.id,
        StrategyPlan(
            options=[
                StrategyOption(
                    forum=ForumType.CONSUMER_COURT, description="x", estimated_cost_inr=100.0,
                    estimated_time="2 weeks", difficulty="low", success_probability=60.0,
                )
            ],
            recommended_option_index=0,
            reasoning="x",
        ),
    )

    from app.domain.entities.evidence import EvidenceSubmission

    await evidence_repo.add_items(
        case.id, [EvidenceSubmission(evidence_type="photo", description="new evidence")]
    )

    stale = await service.get_stale_stages(case.id)
    assert set(stale) == {"risk", "strategy"}


async def test_stale_stages_empty_when_documents_only() -> None:
    # Documents aren't part of the staleness rule (§5.3 only discusses
    # risk/strategy relative to evidence) — sanity check that adding
    # documents alone doesn't spuriously mark anything stale.
    service, case_repo, evidence_repo = _build_service()
    case = await service.create_case(uuid4())

    from app.domain.entities.evidence import EvidenceSubmission

    await evidence_repo.add_items(
        case.id, [EvidenceSubmission(evidence_type="photo", description="evidence")]
    )
    await case_repo.add_documents(
        case.id,
        [GeneratedDocument(document_type=DocumentType.LEGAL_NOTICE, title="x", content="y")],
    )

    assert await service.get_stale_stages(case.id) == []


async def test_save_and_get_timeline() -> None:
    service, _, _ = _build_service()
    case = await service.create_case(uuid4())

    timeline = Timeline(
        events=[
            TimelineEvent(description="second event", sequence_order=2),
            TimelineEvent(description="first event", sequence_order=1),
        ],
        reconstructed_summary="x",
    )
    saved = await service.save_timeline(case.id, timeline)

    assert len(saved) == 2
    fetched = await service.get_timeline(case.id)
    assert [e.sequence_order for e in fetched] == [1, 2]


async def test_get_timeline_empty_for_new_case() -> None:
    service, _, _ = _build_service()
    case = await service.create_case(uuid4())

    assert await service.get_timeline(case.id) == []


async def test_save_and_get_latest_legal_research() -> None:
    from app.schemas.legal_research import LegalCitation, LegalProvision, LegalResearchResult

    service, _, _ = _build_service()
    case = await service.create_case(uuid4())

    result = LegalResearchResult(
        applicable_laws=[
            LegalProvision(
                title="Consumer complaints",
                plain_explanation="x",
                citations=[LegalCitation(act_name="Consumer Protection Act, 2019", section="Section 35")],
            )
        ],
        overall_summary="summary",
    )
    saved = await service.save_legal_research(case.id, result)

    assert saved.jurisdiction == "India"
    latest = await service.get_latest_legal_research(case.id)
    assert latest is not None
    assert latest.plain_explanation == "summary"


async def test_get_latest_legal_research_none_when_absent() -> None:
    service, _, _ = _build_service()
    case = await service.create_case(uuid4())

    assert await service.get_latest_legal_research(case.id) is None


async def test_set_evidence_pause_state() -> None:
    service, _, _ = _build_service()
    case = await service.create_case(uuid4())

    await service.set_evidence_pause_state(
        case.id, awaiting_evidence_upload=True, evidence_pause_count=1
    )

    fetched = await service.get_case(case.id)
    assert fetched.awaiting_evidence_upload is True
    assert fetched.evidence_pause_count == 1


async def test_save_and_get_latest_risk_score() -> None:
    service, _, _ = _build_service()
    case = await service.create_case(uuid4())

    risk = RiskAssessment(
        financial_risk=20.0,
        criminal_risk=5.0,
        urgency="medium",
        needs_police=False,
        needs_lawyer=True,
        needs_medical=False,
        settlement_probability=55.0,
        case_strength=65.0,
        rationale="documentary evidence supports the claim",
    )
    saved = await service.save_risk_score(case.id, risk)

    assert saved.case_strength == 65.0
    assert saved.rationale == "documentary evidence supports the claim"
    latest = await service.get_latest_risk_score(case.id)
    assert latest is not None
    assert latest.needs_lawyer is True


async def test_get_latest_risk_score_none_when_absent() -> None:
    service, _, _ = _build_service()
    case = await service.create_case(uuid4())

    assert await service.get_latest_risk_score(case.id) is None


async def test_list_and_save_citation_verifications() -> None:
    from app.schemas.legal_research import LegalCitation, LegalProvision, LegalResearchResult
    from app.schemas.verification import CitationVerification, VerificationStatus

    service, _, _ = _build_service()
    case = await service.create_case(uuid4())

    result = LegalResearchResult(
        applicable_laws=[
            LegalProvision(
                title="Consumer complaints",
                plain_explanation="x",
                citations=[
                    LegalCitation(act_name="Consumer Protection Act, 2019", section="Section 35")
                ],
            )
        ],
        overall_summary="x",
    )
    saved = await service.save_legal_research(case.id, result)

    citations = await service.list_legal_citations(saved.id)
    assert len(citations) == 1
    assert citations[0].verification_status == "unverified"

    updated = await service.save_citation_verifications(
        saved.id,
        [
            CitationVerification(
                citation=LegalCitation(
                    act_name="Consumer Protection Act, 2019", section="Section 35"
                ),
                status=VerificationStatus.VERIFIED,
                verification_notes="Confirmed against retrieved chunk.",
            )
        ],
    )

    assert updated[0].is_verified is True
    assert updated[0].verification_status == "verified"
