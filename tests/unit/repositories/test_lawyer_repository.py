from __future__ import annotations

from uuid import uuid4

from app import models
from app.repositories.sqlalchemy_lawyer_repository import SqlAlchemyLawyerRepository


async def _create_case(session) -> models.Case:
    user = models.User(email=f"{uuid4()}@example.com", hashed_password="x")
    session.add(user)
    await session.flush()
    case = models.Case(user_id=user.id, status="intake_in_progress")
    session.add(case)
    await session.flush()
    return case


async def _create_lawyer(session, **overrides) -> models.Lawyer:
    defaults = dict(
        full_name="Adv. Test",
        specialization="consumer",
        city="Delhi",
        languages=["en", "hi"],
        fee_range_min=1000.0,
        fee_range_max=5000.0,
        rating=4.5,
        years_experience=10,
    )
    defaults.update(overrides)
    lawyer = models.Lawyer(**defaults)
    session.add(lawyer)
    await session.flush()
    return lawyer


async def test_search_filters_by_city_specialization_and_rating(session) -> None:
    await _create_lawyer(session, city="Delhi", specialization="consumer", rating=4.5)
    await _create_lawyer(session, city="Mumbai", specialization="consumer", rating=4.8)
    await _create_lawyer(session, city="Delhi", specialization="criminal", rating=3.0)
    await session.commit()

    repo = SqlAlchemyLawyerRepository(session)
    results = await repo.search(city="Delhi", specialization="consumer", min_rating=4.0)

    assert len(results) == 1
    assert results[0].city == "Delhi"
    assert results[0].fee_range_inr == (1000.0, 5000.0)


async def test_search_by_language_filters_client_side(session) -> None:
    await _create_lawyer(session, languages=["en", "hi"])
    await _create_lawyer(session, languages=["en", "ta"])
    await session.commit()

    repo = SqlAlchemyLawyerRepository(session)
    results = await repo.search(language="ta")

    assert len(results) == 1
    assert "ta" in results[0].languages


async def test_get_returns_none_for_unknown_lawyer(session) -> None:
    repo = SqlAlchemyLawyerRepository(session)
    assert await repo.get(uuid4()) is None


async def test_record_match_and_list_matches_for_case(session) -> None:
    case = await _create_case(session)
    lawyer = await _create_lawyer(session)
    await session.commit()

    repo = SqlAlchemyLawyerRepository(session)
    await repo.record_match(case.id, lawyer.id, match_score=88.0, match_reason="specialization fit")
    await session.commit()

    matches = await repo.list_matches_for_case(case.id)
    assert len(matches) == 1
    assert matches[0].lawyer.id == lawyer.id
    assert matches[0].match_score == 88.0
