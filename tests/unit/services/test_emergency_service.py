from __future__ import annotations

from uuid import uuid4

from app.schemas.emergency import (
    EmergencyAssessment,
    EmergencyCategory,
    EmergencyGuidance,
    HelplineInfo,
)
from app.services.emergency_service import EmergencyService
from tests.unit.services.fakes import FakeEmergencyRepository


async def test_record_assessment_without_guidance() -> None:
    repo = FakeEmergencyRepository()
    service = EmergencyService(repo)
    case_id = uuid4()

    assessment = EmergencyAssessment(
        is_emergency=False, category=EmergencyCategory.NONE, severity="low", rationale="routine"
    )
    saved = await service.record_assessment(case_id, assessment)

    assert saved.is_emergency is False
    assert saved.immediate_steps is None


async def test_record_assessment_with_guidance() -> None:
    repo = FakeEmergencyRepository()
    service = EmergencyService(repo)
    case_id = uuid4()

    assessment = EmergencyAssessment(
        is_emergency=True, category=EmergencyCategory.DOMESTIC_VIOLENCE, severity="critical",
        rationale="ongoing abuse described",
    )
    guidance = EmergencyGuidance(
        immediate_steps=["Move to a safe location"],
        evidence_preservation_checklist=["Photograph injuries"],
        helplines=[HelplineInfo(name="Women's Helpline", phone="181", available="24x7")],
        recommended_authorities=["Local Police Station"],
    )
    saved = await service.record_assessment(case_id, assessment, guidance)

    assert saved.immediate_steps == ["Move to a safe location"]
    assert saved.helplines is not None
    assert saved.helplines[0]["phone"] == "181"


async def test_get_latest_assessment_returns_most_recent() -> None:
    repo = FakeEmergencyRepository()
    service = EmergencyService(repo)
    case_id = uuid4()

    await service.record_assessment(
        case_id,
        EmergencyAssessment(is_emergency=False, category=EmergencyCategory.NONE, severity="low", rationale="turn 1"),
    )
    await service.record_assessment(
        case_id,
        EmergencyAssessment(
            is_emergency=True, category=EmergencyCategory.KIDNAPPING, severity="critical",
            rationale="turn 2 escalated",
        ),
    )

    latest = await service.get_latest_assessment(case_id)
    assert latest is not None
    assert latest.rationale == "turn 2 escalated"


async def test_get_latest_assessment_none_when_absent() -> None:
    repo = FakeEmergencyRepository()
    service = EmergencyService(repo)

    assert await service.get_latest_assessment(uuid4()) is None
