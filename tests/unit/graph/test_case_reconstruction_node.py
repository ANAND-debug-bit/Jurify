from __future__ import annotations

from uuid import uuid4

from app.agents.case_reconstruction_agent import CaseReconstructionAgent
from app.graph.nodes.case_reconstruction_node import make_case_reconstruction_node
from app.graph.state import create_initial_state
from app.schemas._common import CaseStatus
from app.schemas.language import SupportedLanguage
from app.schemas.timeline import Timeline, TimelineEvent
from app.services.case_service import CaseService
from tests.unit.agents.fakes import FakeStructuredChatModel
from tests.unit.services.fakes import FakeCaseRepository, FakeEvidenceRepository


async def test_node_saves_timeline_and_advances_status() -> None:
    timeline = Timeline(
        events=[TimelineEvent(description="event", sequence_order=1)],
        reconstructed_summary="summary",
    )
    llm = FakeStructuredChatModel(responses=[timeline])
    agent = CaseReconstructionAgent(llm, model_name="fake-model")
    case_repo = FakeCaseRepository()
    service = CaseService(case_repo, FakeEvidenceRepository())
    node = make_case_reconstruction_node(agent, service)

    case = await case_repo.create(uuid4(), SupportedLanguage.EN)
    state = create_initial_state(case.id, uuid4())

    update = await node(state)

    assert update["status"] == CaseStatus.RESEARCHING
    assert update["timeline"] == timeline
    saved = await service.get_timeline(case.id)
    assert len(saved) == 1
