from __future__ import annotations

from uuid import uuid4

from app.schemas.explainability import ExplainabilityItem, ExplainabilityReport
from app.services.explainability_service import ExplainabilityService
from tests.unit.services.fakes import FakeCaseRepository


async def test_record_items_and_get_latest() -> None:
    repo = FakeCaseRepository()
    service = ExplainabilityService(repo)
    case_id = uuid4()

    report = ExplainabilityReport(
        items=[
            ExplainabilityItem(
                conclusion="Recommended forum: Consumer Court",
                reasoning="Best fit given the dispute value",
                supporting_evidence_refs=["evidence-1"],
                supporting_legal_refs=["provision-1"],
                confidence_score=85.0,
            )
        ]
    )
    added = await service.record_items(case_id, report)

    assert added[0].conclusion == "Recommended forum: Consumer Court"
    latest = await service.get_latest(case_id)
    assert len(latest) == 1


async def test_get_latest_empty_when_absent() -> None:
    repo = FakeCaseRepository()
    service = ExplainabilityService(repo)

    assert await service.get_latest(uuid4()) == []
