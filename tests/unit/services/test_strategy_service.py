from __future__ import annotations

from uuid import uuid4

from app.schemas.strategy import ForumType, StrategyOption, StrategyPlan
from app.services.strategy_service import StrategyService
from tests.unit.services.fakes import FakeCaseRepository


async def test_record_plan_marks_recommended_option() -> None:
    repo = FakeCaseRepository()
    service = StrategyService(repo)
    case_id = uuid4()

    plan = StrategyPlan(
        options=[
            StrategyOption(
                forum=ForumType.CONSUMER_COURT, description="a", estimated_cost_inr=1000.0,
                estimated_time="2 weeks", difficulty="low", success_probability=80.0,
            ),
            StrategyOption(
                forum=ForumType.CIVIL_COURT, description="b", estimated_cost_inr=5000.0,
                estimated_time="6 months", difficulty="high", success_probability=40.0,
            ),
        ],
        recommended_option_index=1,
        reasoning="x",
    )
    strategies = await service.record_plan(case_id, plan)

    recommended = [s for s in strategies if s.is_recommended]
    assert len(recommended) == 1
    assert recommended[0].forum == "civil_court"

    latest = await service.get_latest(case_id)
    assert len(latest) == 2


async def test_get_latest_empty_when_absent() -> None:
    repo = FakeCaseRepository()
    service = StrategyService(repo)

    assert await service.get_latest(uuid4()) == []
