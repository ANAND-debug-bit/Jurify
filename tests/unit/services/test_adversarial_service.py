from __future__ import annotations

from uuid import uuid4

from app.schemas.language import SupportedLanguage
from app.services.adversarial_service import AdversarialService
from tests.unit.services.fakes import FakeCaseRepository


async def test_request_stress_test_sets_flag() -> None:
    repo = FakeCaseRepository()
    service = AdversarialService(repo)
    case = await repo.create(uuid4(), SupportedLanguage.EN)
    assert case.stress_test_requested is False

    await service.request_stress_test(case.id)

    fetched = await repo.get(case.id)
    assert fetched is not None
    assert fetched.stress_test_requested is True


async def test_list_rounds_empty_before_stress_test_runs() -> None:
    repo = FakeCaseRepository()
    service = AdversarialService(repo)
    case = await repo.create(uuid4(), SupportedLanguage.EN)

    assert await service.list_rounds(case.id) == []


async def test_list_rounds_after_rounds_added() -> None:
    repo = FakeCaseRepository()
    service = AdversarialService(repo)
    case = await repo.create(uuid4(), SupportedLanguage.EN)
    await repo.add_opposition_round(case.id, round_number=1, role="opposition", content={})
    await repo.add_opposition_round(case.id, round_number=1, role="counter", content={})

    rounds = await service.list_rounds(case.id)
    assert [r.role for r in rounds] == ["opposition", "counter"]
