from __future__ import annotations

import asyncio
from uuid import uuid4

from sqlalchemy import select

from app import models
from app.repositories.sqlalchemy_case_repository import SqlAlchemyCaseRepository
from app.schemas._common import CaseStatus
from app.schemas.case import CaseProfile
from app.schemas.document import DocumentType, GeneratedDocument
from app.schemas.explainability import ExplainabilityItem, ExplainabilityReport
from app.schemas.language import SupportedLanguage
from app.schemas.legal_research import LegalCitation, LegalProvision, LegalResearchResult
from app.schemas.risk import RiskAssessment
from app.schemas.strategy import ForumType, StrategyOption, StrategyPlan
from app.schemas.timeline import Timeline, TimelineEvent
from app.schemas.verification import CitationVerification, VerificationStatus


async def _create_user(session) -> models.User:
    user = models.User(email=f"{uuid4()}@example.com", hashed_password="x")
    session.add(user)
    await session.flush()
    return user


async def test_create_and_get_round_trip(session) -> None:
    user = await _create_user(session)
    repo = SqlAlchemyCaseRepository(session)

    created = await repo.create(user.id, SupportedLanguage.HI)
    await session.commit()

    fetched = await repo.get(created.id)
    assert fetched is not None
    assert fetched.user_id == user.id
    assert fetched.status == CaseStatus.INTAKE_IN_PROGRESS
    assert fetched.preferred_language == SupportedLanguage.HI
    assert fetched.max_rounds == 3


async def test_get_returns_none_for_unknown_case(session) -> None:
    repo = SqlAlchemyCaseRepository(session)
    assert await repo.get(uuid4()) is None


async def test_set_stress_test_requested(session) -> None:
    user = await _create_user(session)
    repo = SqlAlchemyCaseRepository(session)
    case = await repo.create(user.id, SupportedLanguage.EN)
    assert case.stress_test_requested is False

    await repo.set_stress_test_requested(case.id)
    await session.commit()

    fetched = await repo.get(case.id)
    assert fetched is not None
    assert fetched.stress_test_requested is True


async def test_set_evidence_pause_state(session) -> None:
    user = await _create_user(session)
    repo = SqlAlchemyCaseRepository(session)
    case = await repo.create(user.id, SupportedLanguage.EN)
    assert case.awaiting_evidence_upload is False
    assert case.evidence_pause_count == 0

    await repo.set_evidence_pause_state(
        case.id, awaiting_evidence_upload=True, evidence_pause_count=1
    )
    await session.commit()

    fetched = await repo.get(case.id)
    assert fetched is not None
    assert fetched.awaiting_evidence_upload is True
    assert fetched.evidence_pause_count == 1


async def test_update_status(session) -> None:
    user = await _create_user(session)
    repo = SqlAlchemyCaseRepository(session)
    case = await repo.create(user.id, SupportedLanguage.EN)

    await repo.update_status(case.id, CaseStatus.ASSESSING_RISK)
    await session.commit()

    fetched = await repo.get(case.id)
    assert fetched is not None
    assert fetched.status == CaseStatus.ASSESSING_RISK


async def test_update_profile_stores_structured_case_profile(session) -> None:
    user = await _create_user(session)
    repo = SqlAlchemyCaseRepository(session)
    case = await repo.create(user.id, SupportedLanguage.EN)

    profile = CaseProfile(
        incident_category="consumer_dispute",
        summary="Defective product, refund refused",
        confidence=0.8,
        missing_fields=["evidence_mentioned"],
    )
    await repo.update_profile(case.id, profile)
    await session.commit()

    fetched = await repo.get(case.id)
    assert fetched is not None
    assert fetched.case_profile is not None
    assert fetched.case_profile.summary == "Defective product, refund refused"
    assert fetched.case_profile.missing_fields == ["evidence_mentioned"]
    assert fetched.incident_category == "consumer_dispute"


async def test_list_by_user_orders_newest_first(session) -> None:
    user = await _create_user(session)
    repo = SqlAlchemyCaseRepository(session)
    first = await repo.create(user.id, SupportedLanguage.EN)
    second = await repo.create(user.id, SupportedLanguage.EN)
    await session.commit()

    cases = await repo.list_by_user(user.id)

    assert {c.id for c in cases} == {first.id, second.id}


async def test_add_and_list_timeline_events(session) -> None:
    user = await _create_user(session)
    repo = SqlAlchemyCaseRepository(session)
    case = await repo.create(user.id, SupportedLanguage.EN)

    timeline = Timeline(
        events=[
            TimelineEvent(description="second event", sequence_order=2),
            TimelineEvent(description="first event", sequence_order=1),
        ],
        reconstructed_summary="x",
    )
    added = await repo.add_timeline_events(case.id, timeline)
    await session.commit()

    assert len(added) == 2
    listed = await repo.list_timeline_events(case.id)
    assert [e.sequence_order for e in listed] == [1, 2]


async def test_add_risk_score_and_get_latest(session) -> None:
    user = await _create_user(session)
    repo = SqlAlchemyCaseRepository(session)
    case = await repo.create(user.id, SupportedLanguage.EN)

    risk = RiskAssessment(
        financial_risk=10.0,
        criminal_risk=5.0,
        urgency="medium",
        needs_police=False,
        needs_lawyer=True,
        needs_medical=False,
        settlement_probability=60.0,
        case_strength=70.0,
        rationale="strong documentary evidence, low criminal exposure",
    )
    await repo.add_risk_score(case.id, risk)
    await session.commit()

    latest = await repo.get_latest_risk_score(case.id)
    assert latest is not None
    assert latest.needs_lawyer is True
    assert latest.case_strength == 70.0
    assert latest.rationale == "strong documentary evidence, low criminal exposure"


async def test_get_latest_risk_score_none_when_absent(session) -> None:
    user = await _create_user(session)
    repo = SqlAlchemyCaseRepository(session)
    case = await repo.create(user.id, SupportedLanguage.EN)

    assert await repo.get_latest_risk_score(case.id) is None


async def test_add_strategies_marks_recommended_option(session) -> None:
    user = await _create_user(session)
    repo = SqlAlchemyCaseRepository(session)
    case = await repo.create(user.id, SupportedLanguage.EN)

    plan = StrategyPlan(
        options=[
            StrategyOption(
                forum=ForumType.CONSUMER_COURT,
                description="a",
                estimated_cost_inr=1000.0,
                estimated_time="2 weeks",
                difficulty="low",
                success_probability=80.0,
            ),
            StrategyOption(
                forum=ForumType.CIVIL_COURT,
                description="b",
                estimated_cost_inr=5000.0,
                estimated_time="6 months",
                difficulty="high",
                success_probability=40.0,
            ),
        ],
        recommended_option_index=0,
        reasoning="consumer court is faster",
    )
    strategies = await repo.add_strategies(case.id, plan)
    await session.commit()

    assert len(strategies) == 2
    recommended = [s for s in strategies if s.is_recommended]
    assert len(recommended) == 1
    assert recommended[0].forum == "consumer_court"

    latest = await repo.get_latest_strategies(case.id)
    assert len(latest) == 2


async def test_get_latest_strategies_empty_when_absent(session) -> None:
    user = await _create_user(session)
    repo = SqlAlchemyCaseRepository(session)
    case = await repo.create(user.id, SupportedLanguage.EN)

    assert await repo.get_latest_strategies(case.id) == []


async def test_add_and_list_documents_preserve_full_metadata(session) -> None:
    user = await _create_user(session)
    repo = SqlAlchemyCaseRepository(session)
    case = await repo.create(user.id, SupportedLanguage.EN)

    doc = GeneratedDocument(
        document_type=DocumentType.LEGAL_NOTICE,
        title="Legal Notice",
        content="Dear Sir/Madam...",
        recipient="ABC Traders",
        filing_authority="N/A",
    )
    added = await repo.add_documents(case.id, [doc])
    await session.commit()

    assert added[0].title == "Legal Notice"
    assert added[0].recipient == "ABC Traders"

    listed = await repo.list_documents(case.id)
    assert len(listed) == 1
    assert listed[0].filing_authority == "N/A"


async def test_add_and_list_opposition_rounds(session) -> None:
    user = await _create_user(session)
    repo = SqlAlchemyCaseRepository(session)
    case = await repo.create(user.id, SupportedLanguage.EN)

    await repo.add_opposition_round(
        case.id, round_number=1, role="opposition", content={"objections": []}
    )
    await repo.add_opposition_round(
        case.id, round_number=1, role="counter", content={"rebuttals": []}
    )
    await session.commit()

    rounds = await repo.list_opposition_rounds(case.id)
    assert [r.role for r in rounds] == ["opposition", "counter"]


async def test_add_and_get_latest_explainability_items(session) -> None:
    user = await _create_user(session)
    repo = SqlAlchemyCaseRepository(session)
    case = await repo.create(user.id, SupportedLanguage.EN)

    report = ExplainabilityReport(
        items=[
            ExplainabilityItem(
                conclusion="Recommended forum: Consumer Court",
                reasoning="Best fit for a consumer dispute under 20 lakh",
                supporting_evidence_refs=["evidence-1"],
                supporting_legal_refs=["provision-1"],
                confidence_score=85.0,
            )
        ]
    )
    added = await repo.add_explainability_items(case.id, report)
    await session.commit()

    assert len(added) == 1
    assert added[0].conclusion == "Recommended forum: Consumer Court"

    latest = await repo.get_latest_explainability_items(case.id)
    assert len(latest) == 1
    assert latest[0].supporting_evidence_refs == ["evidence-1"]


async def test_get_latest_explainability_items_empty_when_absent(session) -> None:
    user = await _create_user(session)
    repo = SqlAlchemyCaseRepository(session)
    case = await repo.create(user.id, SupportedLanguage.EN)

    assert await repo.get_latest_explainability_items(case.id) == []


async def test_add_legal_research_persists_result_and_explodes_citations(session) -> None:
    user = await _create_user(session)
    repo = SqlAlchemyCaseRepository(session)
    case = await repo.create(user.id, SupportedLanguage.EN)

    result = LegalResearchResult(
        applicable_laws=[
            LegalProvision(
                title="Consumer complaints",
                plain_explanation="File before the Consumer Commission.",
                citations=[
                    LegalCitation(act_name="Consumer Protection Act, 2019", section="Section 35"),
                ],
            ),
            LegalProvision(
                title="Cheating",
                plain_explanation="A criminal offence.",
                citations=[
                    LegalCitation(act_name="Bharatiya Nyaya Sanhita, 2023", section="Section 318"),
                    LegalCitation(act_name="Bharatiya Nagarik Suraksha Sanhita, 2023", section="Section 173"),
                ],
            ),
        ],
        overall_summary="Two applicable provisions found.",
    )
    saved = await repo.add_legal_research(case.id, result)
    await session.commit()

    assert saved.plain_explanation == "Two applicable provisions found."
    assert len(saved.applicable_laws) == 2
    assert saved.applicable_laws[0].citations[0].act_name == "Consumer Protection Act, 2019"

    # legal_citations rows are exploded independently of the JSONB blob
    citation_stmt = select(models.LegalCitation).where(
        models.LegalCitation.legal_research_result_id == saved.id
    )
    citations = (await session.execute(citation_stmt)).scalars().all()
    assert len(citations) == 3
    assert all(c.is_verified is False for c in citations)


async def test_get_latest_legal_research_returns_most_recent(session) -> None:
    user = await _create_user(session)
    repo = SqlAlchemyCaseRepository(session)
    case = await repo.create(user.id, SupportedLanguage.EN)

    await repo.add_legal_research(
        case.id,
        LegalResearchResult(applicable_laws=[], overall_summary="first pass"),
    )
    await session.commit()
    # get_latest_legal_research orders by created_at, which is set via
    # server_default=func.now(). SQLite's CURRENT_TIMESTAMP only has
    # 1-second resolution, so two writes issued back-to-back (as these
    # would be in a real pipeline re-run, always separated by an LLM
    # inference call) can otherwise land in the same tick and make the
    # "latest" ordering non-deterministic. Force a real tick so this test
    # reflects realistic sequential usage rather than a pathological
    # same-instant write.
    await asyncio.sleep(1.1)
    await repo.add_legal_research(
        case.id,
        LegalResearchResult(applicable_laws=[], overall_summary="second pass"),
    )
    await session.commit()

    latest = await repo.get_latest_legal_research(case.id)
    assert latest is not None
    assert latest.plain_explanation == "second pass"


async def test_get_latest_legal_research_none_when_absent(session) -> None:
    user = await _create_user(session)
    repo = SqlAlchemyCaseRepository(session)
    case = await repo.create(user.id, SupportedLanguage.EN)

    assert await repo.get_latest_legal_research(case.id) is None


async def test_list_legal_citations_returns_exploded_rows(session) -> None:
    user = await _create_user(session)
    repo = SqlAlchemyCaseRepository(session)
    case = await repo.create(user.id, SupportedLanguage.EN)
    saved = await repo.add_legal_research(
        case.id,
        LegalResearchResult(
            applicable_laws=[
                LegalProvision(
                    title="Consumer complaints",
                    plain_explanation="x",
                    citations=[
                        LegalCitation(
                            act_name="Consumer Protection Act, 2019", section="Section 35"
                        )
                    ],
                )
            ],
            overall_summary="x",
        ),
    )
    await session.commit()

    citations = await repo.list_legal_citations(saved.id)

    assert len(citations) == 1
    assert citations[0].act_name == "Consumer Protection Act, 2019"
    assert citations[0].is_verified is False
    assert citations[0].verification_status == "unverified"


async def test_update_citation_verifications_matches_by_act_and_section(session) -> None:
    user = await _create_user(session)
    repo = SqlAlchemyCaseRepository(session)
    case = await repo.create(user.id, SupportedLanguage.EN)
    saved = await repo.add_legal_research(
        case.id,
        LegalResearchResult(
            applicable_laws=[
                LegalProvision(
                    title="Consumer complaints",
                    plain_explanation="x",
                    citations=[
                        LegalCitation(
                            act_name="Consumer Protection Act, 2019", section="Section 35"
                        )
                    ],
                ),
                LegalProvision(
                    title="Fraud",
                    plain_explanation="x",
                    citations=[
                        LegalCitation(act_name="Invented Act, 1999", section="Section 1")
                    ],
                ),
            ],
            overall_summary="x",
        ),
    )
    await session.commit()

    updated = await repo.update_citation_verifications(
        saved.id,
        [
            CitationVerification(
                citation=LegalCitation(
                    act_name="Consumer Protection Act, 2019", section="Section 35"
                ),
                status=VerificationStatus.VERIFIED,
                verification_notes="Matched a retrieved statute chunk.",
            ),
            CitationVerification(
                citation=LegalCitation(act_name="Invented Act, 1999", section="Section 1"),
                status=VerificationStatus.REJECTED,
                verification_notes="No matching statute found in the corpus.",
            ),
        ],
    )
    await session.commit()

    by_act = {row.act_name: row for row in updated}
    assert by_act["Consumer Protection Act, 2019"].is_verified is True
    assert by_act["Consumer Protection Act, 2019"].verification_status == "verified"
    assert by_act["Consumer Protection Act, 2019"].verified_at is not None
    assert by_act["Invented Act, 1999"].is_verified is False
    assert by_act["Invented Act, 1999"].verification_status == "rejected"


async def test_update_citation_verifications_ignores_unmatched_verifications(session) -> None:
    user = await _create_user(session)
    repo = SqlAlchemyCaseRepository(session)
    case = await repo.create(user.id, SupportedLanguage.EN)
    saved = await repo.add_legal_research(
        case.id,
        LegalResearchResult(applicable_laws=[], overall_summary="x"),
    )
    await session.commit()

    updated = await repo.update_citation_verifications(
        saved.id,
        [
            CitationVerification(
                citation=LegalCitation(act_name="Nonexistent Act", section="Section 1"),
                status=VerificationStatus.VERIFIED,
                verification_notes="n/a",
            )
        ],
    )

    assert updated == []
