from sqlalchemy import func, select

from app.models import (
    AgentLog,
    Case,
    CaseLawyerMatch,
    CaseTimelineEvent,
    Complaint,
    ConversationMemory,
    Document,
    EmergencyAssessment,
    Evidence,
    ExplainabilityReport,
    GovernmentSchemeMatch,
    JudgeOpinion,
    Lawyer,
    LegalCitation,
    LegalResearchResult,
    LongTermMemory,
    OppositionRound,
    RiskScore,
    Strategy,
    User,
)
from tests.unit.models.factories import build_full_case_graph

CASE_CHILD_TABLES = [
    CaseTimelineEvent,
    Evidence,
    LegalResearchResult,
    EmergencyAssessment,
    GovernmentSchemeMatch,
    ExplainabilityReport,
    RiskScore,
    Strategy,
    Document,
    Complaint,
    CaseLawyerMatch,
    OppositionRound,
    JudgeOpinion,
    AgentLog,
    ConversationMemory,
]


async def _count(session, model) -> int:
    result = (await session.execute(select(func.count()).select_from(model))).scalar_one()
    return int(result)


async def test_deleting_a_case_cascades_to_every_child_table(session_factory) -> None:
    async with session_factory() as session:
        user_id, case_id = await build_full_case_graph(session)

    async with session_factory() as session:
        for model in CASE_CHILD_TABLES:
            assert await _count(session, model) == 1, f"{model.__name__} should have 1 row before delete"

    async with session_factory() as session:
        case = await session.get(Case, case_id)
        await session.delete(case)
        await session.commit()

    async with session_factory() as session:
        for model in CASE_CHILD_TABLES:
            assert await _count(session, model) == 0, f"{model.__name__} should be cascade-deleted"

        # legal_citations cascades transitively via legal_research_results
        assert await _count(session, LegalCitation) == 0

        # Lawyer is not owned by Case — only the join row (CaseLawyerMatch,
        # already asserted above) is cascade-deleted.
        assert await _count(session, Lawyer) == 1

        # User is the parent, not a child of Case — must survive.
        assert await _count(session, User) == 1


async def test_deleting_a_user_cascades_to_their_cases_and_long_term_memory(session_factory) -> None:
    async with session_factory() as session:
        user_id, case_id = await build_full_case_graph(session)

    async with session_factory() as session:
        user = await session.get(User, user_id)
        await session.delete(user)
        await session.commit()

    async with session_factory() as session:
        assert await session.get(Case, case_id) is None
        assert await _count(session, Case) == 0
        assert await _count(session, LongTermMemory) == 0
        for model in CASE_CHILD_TABLES:
            assert await _count(session, model) == 0, f"{model.__name__} should cascade via Case"

        # Lawyer is independent of both User and Case.
        assert await _count(session, Lawyer) == 1
