"""Test-only helpers for building a fully connected object graph across
all 20 tables — shared by the relationship, cascade, and constraint
tests so each test only sets up what it specifically needs on top."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

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


async def create_user(session: AsyncSession, *, email: str = "user@example.com") -> User:
    user = User(email=email, hashed_password="hashed-password")
    session.add(user)
    await session.flush()
    return user


async def create_case(session: AsyncSession, user: User, *, status: str = "intake_in_progress") -> Case:
    case = Case(user_id=user.id, status=status, case_profile={"summary": "test case"})
    session.add(case)
    await session.flush()
    return case


async def build_full_case_graph(session: AsyncSession) -> tuple[uuid.UUID, uuid.UUID]:
    """Creates one row in every case-linked table (plus a Lawyer and its
    match), commits, and returns (user_id, case_id)."""
    user = await create_user(session)
    case = await create_case(session, user)

    legal_research = LegalResearchResult(case_id=case.id, applicable_laws={"laws": []})
    document = Document(case_id=case.id, document_type="legal_notice", content="draft content")
    lawyer = Lawyer(full_name="Adv. Test", city="Delhi", specialization="consumer")
    session.add_all([legal_research, document, lawyer])
    await session.flush()

    session.add_all(
        [
            CaseTimelineEvent(case_id=case.id, description="incident occurred", sequence_order=1),
            Evidence(case_id=case.id, evidence_type="photo", description="photo of damage"),
            LegalCitation(
                legal_research_result_id=legal_research.id, act_name="BNS", section="103"
            ),
            EmergencyAssessment(case_id=case.id, category="none", severity="low"),
            GovernmentSchemeMatch(case_id=case.id, scheme_name="free_legal_aid", eligible=True),
            ExplainabilityReport(case_id=case.id, conclusion="recommended forum: consumer court"),
            RiskScore(case_id=case.id, financial_risk=10.0, case_strength=70.0),
            Strategy(case_id=case.id, forum="consumer_court", is_recommended=True),
            Complaint(case_id=case.id, document_id=document.id, filed_with="District Consumer Forum"),
            CaseLawyerMatch(case_id=case.id, lawyer_id=lawyer.id, match_score=90.0),
            OppositionRound(case_id=case.id, round_number=1, role="opposition", content={"objections": []}),
            JudgeOpinion(case_id=case.id, likely_outcome="favorable"),
            ConversationMemory(case_id=case.id, role="user", content="hello", language="en"),
            AgentLog(case_id=case.id, agent_name="supervisor", status="success"),
            LongTermMemory(user_id=user.id, memory_type="case_summary", content={"note": "x"}),
        ]
    )
    await session.commit()
    return user.id, case.id
