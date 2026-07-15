from __future__ import annotations

from uuid import uuid4

from app.graph.nodes.awaiting_evidence_upload_node import make_awaiting_evidence_upload_node
from app.graph.state import create_initial_state
from app.schemas._common import CaseStatus
from app.schemas.language import SupportedLanguage
from app.services.case_service import CaseService
from tests.unit.services.fakes import FakeCaseRepository, FakeEvidenceRepository


async def test_node_marks_case_paused_and_increments_count() -> None:
    case_repo = FakeCaseRepository()
    service = CaseService(case_repo, FakeEvidenceRepository())
    node = make_awaiting_evidence_upload_node(service)

    case = await case_repo.create(uuid4(), SupportedLanguage.EN)
    state = create_initial_state(case.id, uuid4())
    state["evidence_pause_count"] = 0

    update = await node(state)

    assert update["status"] == CaseStatus.AWAITING_EVIDENCE_UPLOAD
    assert update["awaiting_evidence_upload"] is True
    assert update["evidence_pause_count"] == 1

    fetched = await service.get_case(case.id)
    assert fetched.awaiting_evidence_upload is True
    assert fetched.evidence_pause_count == 1


async def test_node_increments_from_existing_pause_count() -> None:
    case_repo = FakeCaseRepository()
    service = CaseService(case_repo, FakeEvidenceRepository())
    node = make_awaiting_evidence_upload_node(service)

    case = await case_repo.create(uuid4(), SupportedLanguage.EN)
    state = create_initial_state(case.id, uuid4())
    state["evidence_pause_count"] = 1

    update = await node(state)

    assert update["evidence_pause_count"] == 2
