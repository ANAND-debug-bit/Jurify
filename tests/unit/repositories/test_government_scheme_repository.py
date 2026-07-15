from __future__ import annotations

from uuid import uuid4

from app import models
from app.repositories.sqlalchemy_government_scheme_repository import (
    SqlAlchemyGovernmentSchemeRepository,
)
from app.schemas.government_scheme import (
    GovernmentScheme,
    GovernmentSchemeMatch,
    GovernmentSchemeReport,
)


async def _create_case(session) -> models.Case:
    user = models.User(email=f"{uuid4()}@example.com", hashed_password="x")
    session.add(user)
    await session.flush()
    case = models.Case(user_id=user.id, status="intake_in_progress")
    session.add(case)
    await session.flush()
    return case


async def test_add_matches_and_get_latest(session) -> None:
    case = await _create_case(session)
    repo = SqlAlchemyGovernmentSchemeRepository(session)

    report = GovernmentSchemeReport(
        matches=[
            GovernmentSchemeMatch(
                scheme=GovernmentScheme.FREE_LEGAL_AID,
                eligible=True,
                confidence=80.0,
                documents_required=["income certificate"],
                how_to_apply="Visit DLSA",
                relevant_authority="DLSA",
            ),
            GovernmentSchemeMatch(
                scheme=GovernmentScheme.AYUSHMAN_BHARAT,
                eligible=False,
                confidence=10.0,
                documents_required=[],
                how_to_apply="N/A",
                relevant_authority="N/A",
            ),
        ]
    )
    added = await repo.add_matches(case.id, report)
    await session.commit()

    assert len(added) == 2
    latest = await repo.get_latest_matches(case.id)
    assert len(latest) == 2
    assert {m.scheme.value for m in latest} == {"free_legal_aid", "ayushman_bharat"}


async def test_get_latest_matches_empty_when_absent(session) -> None:
    case = await _create_case(session)
    repo = SqlAlchemyGovernmentSchemeRepository(session)

    assert await repo.get_latest_matches(case.id) == []
