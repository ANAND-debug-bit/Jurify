from __future__ import annotations

import asyncio
from uuid import uuid4

from app import models
from app.domain.entities.evidence import EvidenceSubmission
from app.repositories.sqlalchemy_evidence_repository import SqlAlchemyEvidenceRepository
from app.schemas._common import UrgencyLevel
from app.schemas.evidence import EvidenceGap, EvidenceItem, EvidenceQuality, EvidenceReport


async def _create_case(session) -> models.Case:
    user = models.User(email=f"{uuid4()}@example.com", hashed_password="x")
    session.add(user)
    await session.flush()
    case = models.Case(user_id=user.id, status="intake_in_progress")
    session.add(case)
    await session.flush()
    return case


async def test_add_items_and_list_by_case(session) -> None:
    case = await _create_case(session)
    repo = SqlAlchemyEvidenceRepository(session)

    added = await repo.add_items(
        case.id,
        [
            EvidenceSubmission(evidence_type="photo", description="damaged item", file_url="https://x/1.jpg"),
            EvidenceSubmission(evidence_type="receipt", description="purchase receipt"),
        ],
    )
    await session.commit()

    assert len(added) == 2
    listed = await repo.list_by_case(case.id)
    assert {item.evidence_type for item in listed} == {"photo", "receipt"}


async def test_list_by_case_empty_when_no_evidence(session) -> None:
    case = await _create_case(session)
    repo = SqlAlchemyEvidenceRepository(session)

    assert await repo.list_by_case(case.id) == []


def _report(summary: str) -> EvidenceReport:
    return EvidenceReport(
        submitted_evidence=[
            EvidenceItem(evidence_type="photo", description="damaged item", quality=EvidenceQuality.MODERATE)
        ],
        gaps=[
            EvidenceGap(
                description="No proof of purchase",
                suggested_evidence="Upload the receipt",
                priority=UrgencyLevel.CRITICAL,
            )
        ],
        completeness_score=40.0,
        summary=summary,
    )


async def test_add_report_persists_submitted_evidence_and_gaps(session) -> None:
    case = await _create_case(session)
    repo = SqlAlchemyEvidenceRepository(session)

    saved = await repo.add_report(case.id, _report("initial assessment"))
    await session.commit()

    assert saved.summary == "initial assessment"
    assert saved.completeness_score == 40.0
    assert len(saved.submitted_evidence) == 1
    assert saved.submitted_evidence[0].evidence_type == "photo"
    assert len(saved.gaps) == 1
    assert saved.gaps[0].priority == UrgencyLevel.CRITICAL


async def test_get_latest_report_returns_most_recent(session) -> None:
    case = await _create_case(session)
    repo = SqlAlchemyEvidenceRepository(session)

    await repo.add_report(case.id, _report("first pass"))
    await session.commit()
    # See test_case_repository.py's identical comment on
    # test_get_latest_legal_research_returns_most_recent — SQLite's
    # CURRENT_TIMESTAMP has 1-second resolution, so force a real tick
    # between writes rather than relying on a same-instant ordering tie.
    await asyncio.sleep(1.1)
    await repo.add_report(case.id, _report("second pass"))
    await session.commit()

    latest = await repo.get_latest_report(case.id)
    assert latest is not None
    assert latest.summary == "second pass"


async def test_get_latest_report_none_when_absent(session) -> None:
    case = await _create_case(session)
    repo = SqlAlchemyEvidenceRepository(session)

    assert await repo.get_latest_report(case.id) is None
