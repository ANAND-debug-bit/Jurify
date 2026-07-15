from __future__ import annotations

from uuid import uuid4

from app.domain.entities.lawyer import Lawyer
from app.services.lawyer_service import LawyerService
from tests.unit.services.fakes import FakeLawyerRepository


def _lawyer(**overrides) -> Lawyer:
    defaults = dict(
        id=uuid4(), full_name="Adv. Test", specialization="consumer", city="Delhi",
        languages=["en", "hi"], fee_range_inr=(1000.0, 5000.0), rating=4.5, years_experience=10,
    )
    defaults.update(overrides)
    return Lawyer(**defaults)


async def test_search_filters_by_city_and_specialization() -> None:
    repo = FakeLawyerRepository()
    lawyer_delhi = _lawyer(city="Delhi")
    lawyer_mumbai = _lawyer(city="Mumbai")
    repo.lawyers = {lawyer_delhi.id: lawyer_delhi, lawyer_mumbai.id: lawyer_mumbai}
    service = LawyerService(repo)

    results = await service.search(city="Delhi")

    assert len(results) == 1
    assert results[0].city == "Delhi"


async def test_get_returns_none_for_unknown_lawyer() -> None:
    repo = FakeLawyerRepository()
    service = LawyerService(repo)

    assert await service.get(uuid4()) is None


async def test_record_match_and_list_matches_for_case() -> None:
    repo = FakeLawyerRepository()
    lawyer = _lawyer()
    repo.lawyers = {lawyer.id: lawyer}
    service = LawyerService(repo)
    case_id = uuid4()

    await service.record_match(case_id, lawyer.id, match_score=90.0, match_reason="specialization fit")

    matches = await service.list_matches_for_case(case_id)
    assert len(matches) == 1
    assert matches[0].match_score == 90.0
