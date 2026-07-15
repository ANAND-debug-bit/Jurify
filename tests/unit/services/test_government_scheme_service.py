from __future__ import annotations

from uuid import uuid4

from app.schemas.government_scheme import (
    GovernmentScheme,
    GovernmentSchemeMatch,
    GovernmentSchemeReport,
)
from app.services.government_scheme_service import GovernmentSchemeService
from tests.unit.services.fakes import FakeGovernmentSchemeRepository


async def test_record_matches_and_get_latest() -> None:
    repo = FakeGovernmentSchemeRepository()
    service = GovernmentSchemeService(repo)
    case_id = uuid4()

    report = GovernmentSchemeReport(
        matches=[
            GovernmentSchemeMatch(
                scheme=GovernmentScheme.FREE_LEGAL_AID, eligible=True, confidence=80.0,
                documents_required=["income certificate"], how_to_apply="Visit DLSA",
                relevant_authority="DLSA",
            )
        ]
    )
    added = await service.record_matches(case_id, report)

    assert len(added) == 1
    latest = await service.get_latest(case_id)
    assert latest[0].scheme == GovernmentScheme.FREE_LEGAL_AID


async def test_get_latest_empty_when_absent() -> None:
    repo = FakeGovernmentSchemeRepository()
    service = GovernmentSchemeService(repo)

    assert await service.get_latest(uuid4()) == []
