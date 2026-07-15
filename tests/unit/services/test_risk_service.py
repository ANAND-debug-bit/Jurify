from __future__ import annotations

from uuid import uuid4

from app.schemas.risk import RiskAssessment
from app.services.risk_service import RiskService
from tests.unit.services.fakes import FakeCaseRepository


def _risk(**overrides) -> RiskAssessment:
    defaults = dict(
        financial_risk=10.0, criminal_risk=5.0, urgency="medium", needs_police=False,
        needs_lawyer=True, needs_medical=False, settlement_probability=60.0,
        case_strength=70.0, rationale="x",
    )
    defaults.update(overrides)
    return RiskAssessment(**defaults)


async def test_record_and_get_latest_assessment() -> None:
    repo = FakeCaseRepository()
    service = RiskService(repo)
    case_id = uuid4()

    await service.record_assessment(case_id, _risk(case_strength=40.0))
    await service.record_assessment(case_id, _risk(case_strength=80.0))

    latest = await service.get_latest(case_id)
    assert latest is not None
    assert latest.case_strength == 80.0


async def test_get_latest_none_when_absent() -> None:
    repo = FakeCaseRepository()
    service = RiskService(repo)

    assert await service.get_latest(uuid4()) is None
