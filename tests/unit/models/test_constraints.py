import pytest
from sqlalchemy.exc import IntegrityError

from app.models import JudgeOpinion, LegalCitation, LegalResearchResult, User
from tests.unit.models.factories import create_case, create_user


async def test_judge_opinion_case_id_is_unique(session_factory) -> None:
    async with session_factory() as session:
        user = await create_user(session)
        case = await create_case(session, user)
        session.add(JudgeOpinion(case_id=case.id, likely_outcome="favorable"))
        await session.commit()

    async with session_factory() as session:
        session.add(JudgeOpinion(case_id=case.id, likely_outcome="a second opinion"))
        with pytest.raises(IntegrityError):
            await session.commit()


async def test_user_email_is_unique(session_factory) -> None:
    async with session_factory() as session:
        session.add(User(email="dup@example.com", hashed_password="x"))
        await session.commit()

    async with session_factory() as session:
        session.add(User(email="dup@example.com", hashed_password="y"))
        with pytest.raises(IntegrityError):
            await session.commit()


async def test_legal_citation_verification_defaults(session_factory) -> None:
    async with session_factory() as session:
        user = await create_user(session)
        case = await create_case(session, user)
        research = LegalResearchResult(case_id=case.id)
        session.add(research)
        await session.flush()

        citation = LegalCitation(legal_research_result_id=research.id, act_name="BNS")
        session.add(citation)
        await session.commit()
        await session.refresh(citation)

        assert citation.is_verified is False
        assert citation.verification_status == "unverified"
        assert citation.verified_at is None


async def test_case_control_flags_default_correctly(session_factory) -> None:
    async with session_factory() as session:
        user = await create_user(session)
        case = await create_case(session, user)
        await session.refresh(case)

        assert case.preferred_language == "en"
        assert case.stress_test_requested is False
        assert case.awaiting_evidence_upload is False
        assert case.evidence_pause_count == 0
        assert case.max_rounds == 3
        assert case.round_count == 0
        assert case.created_at is not None
        assert case.updated_at is not None


async def test_jsonb_variant_column_round_trips_nested_structures(session_factory) -> None:
    async with session_factory() as session:
        user = await create_user(session)
        case = await create_case(session, user)
        case.case_profile = {
            "incident_category": "consumer_dispute",
            "parties": [{"role": "complainant", "name": "A"}],
            "facts_collected": {"date": "2026-01-01"},
        }
        await session.commit()

    async with session_factory() as session:
        refetched = await session.get(type(case), case.id)
        assert refetched.case_profile["incident_category"] == "consumer_dispute"
        assert refetched.case_profile["parties"][0]["name"] == "A"


async def test_vector_fallback_column_round_trips_a_float_list(session_factory) -> None:
    from app.models import LongTermMemory

    async with session_factory() as session:
        user = await create_user(session)
        memory = LongTermMemory(
            user_id=user.id, memory_type="case_summary", embedding=[0.1, 0.2, 0.3]
        )
        session.add(memory)
        await session.commit()
        memory_id = memory.id

    async with session_factory() as session:
        refetched = await session.get(LongTermMemory, memory_id)
        assert refetched.embedding == [0.1, 0.2, 0.3]
