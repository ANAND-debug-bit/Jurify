from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models import Case, User
from tests.unit.models.factories import build_full_case_graph


async def test_full_case_graph_relationships_navigate_correctly(session_factory) -> None:
    async with session_factory() as session:
        user_id, case_id = await build_full_case_graph(session)

    async with session_factory() as session:
        stmt = (
            select(Case)
            .where(Case.id == case_id)
            .options(
                selectinload(Case.user),
                selectinload(Case.timeline_events),
                selectinload(Case.evidence_items),
                selectinload(Case.legal_research_results),
                selectinload(Case.emergency_assessments),
                selectinload(Case.government_scheme_matches),
                selectinload(Case.explainability_reports),
                selectinload(Case.risk_scores),
                selectinload(Case.strategies),
                selectinload(Case.documents),
                selectinload(Case.complaints),
                selectinload(Case.lawyer_matches),
                selectinload(Case.opposition_rounds),
                selectinload(Case.judge_opinion),
                selectinload(Case.agent_logs),
                selectinload(Case.conversation_memory),
            )
        )
        case = (await session.execute(stmt)).scalar_one()

        assert case.user.id == user_id
        assert len(case.timeline_events) == 1
        assert len(case.evidence_items) == 1
        assert len(case.legal_research_results) == 1
        assert len(case.emergency_assessments) == 1
        assert len(case.government_scheme_matches) == 1
        assert len(case.explainability_reports) == 1
        assert len(case.risk_scores) == 1
        assert len(case.strategies) == 1
        assert len(case.documents) == 1
        assert len(case.complaints) == 1
        assert len(case.lawyer_matches) == 1
        assert len(case.opposition_rounds) == 1
        assert case.judge_opinion is not None
        assert len(case.agent_logs) == 1
        assert len(case.conversation_memory) == 1

    async with session_factory() as session:
        user_stmt = (
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.cases), selectinload(User.long_term_memories))
        )
        user = (await session.execute(user_stmt)).scalar_one()

        assert len(user.cases) == 1
        assert user.cases[0].id == case_id
        assert len(user.long_term_memories) == 1


async def test_legal_citation_belongs_to_its_research_result(session_factory) -> None:
    from app.models import LegalResearchResult

    async with session_factory() as session:
        _, case_id = await build_full_case_graph(session)

    async with session_factory() as session:
        stmt = (
            select(LegalResearchResult)
            .where(LegalResearchResult.case_id == case_id)
            .options(selectinload(LegalResearchResult.citations))
        )
        research = (await session.execute(stmt)).scalar_one()

        assert len(research.citations) == 1
        assert research.citations[0].act_name == "BNS"
        assert research.citations[0].legal_research_result_id == research.id


async def test_case_lawyer_match_links_case_and_lawyer(session_factory) -> None:
    from app.models import CaseLawyerMatch

    async with session_factory() as session:
        _, case_id = await build_full_case_graph(session)

    async with session_factory() as session:
        stmt = (
            select(CaseLawyerMatch)
            .where(CaseLawyerMatch.case_id == case_id)
            .options(selectinload(CaseLawyerMatch.lawyer), selectinload(CaseLawyerMatch.case))
        )
        match = (await session.execute(stmt)).scalar_one()

        assert match.lawyer.full_name == "Adv. Test"
        assert match.case.id == case_id


async def test_document_complaint_relationship(session_factory) -> None:
    from app.models import Document

    async with session_factory() as session:
        _, case_id = await build_full_case_graph(session)

    async with session_factory() as session:
        stmt = (
            select(Document)
            .where(Document.case_id == case_id)
            .options(selectinload(Document.complaints))
        )
        document = (await session.execute(stmt)).scalar_one()

        assert len(document.complaints) == 1
        assert document.complaints[0].filed_with == "District Consumer Forum"
