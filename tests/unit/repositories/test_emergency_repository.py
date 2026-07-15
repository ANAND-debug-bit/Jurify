from __future__ import annotations

from uuid import uuid4

from app import models
from app.repositories.sqlalchemy_emergency_repository import SqlAlchemyEmergencyRepository
from app.schemas.emergency import (
    EmergencyAssessment,
    EmergencyCategory,
    EmergencyGuidance,
    HelplineInfo,
)


async def _create_case(session) -> models.Case:
    user = models.User(email=f"{uuid4()}@example.com", hashed_password="x")
    session.add(user)
    await session.flush()
    case = models.Case(user_id=user.id, status="intake_in_progress")
    session.add(case)
    await session.flush()
    return case


async def test_add_assessment_without_guidance(session) -> None:
    case = await _create_case(session)
    repo = SqlAlchemyEmergencyRepository(session)

    assessment = EmergencyAssessment(
        is_emergency=False, category=EmergencyCategory.NONE, severity="low", rationale="routine dispute"
    )
    saved = await repo.add_assessment(case.id, assessment)
    await session.commit()

    assert saved.is_emergency is False
    assert saved.rationale == "routine dispute"
    assert saved.immediate_steps is None


async def test_add_assessment_with_guidance_populates_guidance_fields(session) -> None:
    case = await _create_case(session)
    repo = SqlAlchemyEmergencyRepository(session)

    assessment = EmergencyAssessment(
        is_emergency=True,
        category=EmergencyCategory.DOMESTIC_VIOLENCE,
        severity="critical",
        rationale="user described ongoing physical abuse",
    )
    guidance = EmergencyGuidance(
        immediate_steps=["Move to a safe location", "Call 181"],
        evidence_preservation_checklist=["Photograph injuries"],
        helplines=[HelplineInfo(name="Women's Helpline", phone="181", available="24x7")],
        recommended_authorities=["Local Police Station"],
    )
    saved = await repo.add_assessment(case.id, assessment, guidance)
    await session.commit()

    assert saved.is_emergency is True
    assert saved.immediate_steps == ["Move to a safe location", "Call 181"]
    assert saved.helplines is not None
    assert saved.helplines[0]["phone"] == "181"


async def test_get_latest_assessment_returns_most_recent(session) -> None:
    case = await _create_case(session)
    repo = SqlAlchemyEmergencyRepository(session)

    await repo.add_assessment(
        case.id,
        EmergencyAssessment(is_emergency=False, category=EmergencyCategory.NONE, severity="low", rationale="turn 1"),
    )
    await repo.add_assessment(
        case.id,
        EmergencyAssessment(
            is_emergency=True,
            category=EmergencyCategory.ILLEGAL_DETENTION,
            severity="critical",
            rationale="turn 2 escalated",
        ),
    )
    await session.commit()

    latest = await repo.get_latest_assessment(case.id)
    assert latest is not None
    assert latest.rationale == "turn 2 escalated"


async def test_get_latest_assessment_none_when_absent(session) -> None:
    case = await _create_case(session)
    repo = SqlAlchemyEmergencyRepository(session)

    assert await repo.get_latest_assessment(case.id) is None
