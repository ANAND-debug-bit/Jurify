from __future__ import annotations

from uuid import uuid4

from app.domain.entities.evidence import EvidenceSubmission
from app.services.evidence_service import EvidenceService
from tests.unit.services.fakes import FakeEvidenceRepository


async def test_submit_and_list_evidence() -> None:
    repo = FakeEvidenceRepository()
    service = EvidenceService(repo)
    case_id = uuid4()

    added = await service.submit_evidence(
        case_id,
        [
            EvidenceSubmission(evidence_type="photo", description="damaged goods"),
            EvidenceSubmission(evidence_type="receipt", description="purchase proof"),
        ],
    )

    assert len(added) == 2
    listed = await service.list_evidence(case_id)
    assert {item.evidence_type for item in listed} == {"photo", "receipt"}


async def test_list_evidence_empty_for_new_case() -> None:
    repo = FakeEvidenceRepository()
    service = EvidenceService(repo)

    assert await service.list_evidence(uuid4()) == []


async def test_save_and_get_latest_report() -> None:
    from app.schemas._common import UrgencyLevel
    from app.schemas.evidence import EvidenceGap, EvidenceItem, EvidenceQuality, EvidenceReport

    repo = FakeEvidenceRepository()
    service = EvidenceService(repo)
    case_id = uuid4()

    report = EvidenceReport(
        submitted_evidence=[
            EvidenceItem(evidence_type="photo", description="x", quality=EvidenceQuality.WEAK)
        ],
        gaps=[
            EvidenceGap(
                description="missing receipt",
                suggested_evidence="upload receipt",
                priority=UrgencyLevel.CRITICAL,
            )
        ],
        completeness_score=30.0,
        summary="early stage",
    )
    saved = await service.save_report(case_id, report)

    assert saved.completeness_score == 30.0
    latest = await service.get_latest_report(case_id)
    assert latest is not None
    assert latest.summary == "early stage"


async def test_get_latest_report_none_when_absent() -> None:
    repo = FakeEvidenceRepository()
    service = EvidenceService(repo)

    assert await service.get_latest_report(uuid4()) is None
