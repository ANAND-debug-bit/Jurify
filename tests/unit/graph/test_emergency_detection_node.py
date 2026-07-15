from __future__ import annotations

from uuid import uuid4

from app.agents.emergency_detection_agent import EmergencyDetectionAgent
from app.graph.nodes.emergency_detection_node import make_emergency_detection_node
from app.graph.state import create_initial_state
from app.schemas.emergency import EmergencyAssessment, EmergencyCategory
from app.services.emergency_service import EmergencyService
from tests.unit.agents.fakes import FakeStructuredChatModel
from tests.unit.services.fakes import FakeEmergencyRepository


async def test_node_persists_when_no_emergency() -> None:
    assessment = EmergencyAssessment(
        is_emergency=False, category=EmergencyCategory.NONE, severity="low", rationale="routine"
    )
    llm = FakeStructuredChatModel(responses=[assessment])
    agent = EmergencyDetectionAgent(llm, model_name="fake-model")
    repo = FakeEmergencyRepository()
    service = EmergencyService(repo)
    node = make_emergency_detection_node(agent, service)

    case_id = uuid4()
    state = create_initial_state(case_id, uuid4())

    update = await node(state)

    assert update["emergency_assessment"] == assessment
    latest = await service.get_latest_assessment(case_id)
    assert latest is not None
    assert latest.is_emergency is False


async def test_node_does_not_persist_when_emergency_detected() -> None:
    # emergency_agent_node persists the combined row instead — see its
    # own test file for the full round trip.
    assessment = EmergencyAssessment(
        is_emergency=True, category=EmergencyCategory.KIDNAPPING, severity="critical",
        rationale="child reported missing",
    )
    llm = FakeStructuredChatModel(responses=[assessment])
    agent = EmergencyDetectionAgent(llm, model_name="fake-model")
    repo = FakeEmergencyRepository()
    service = EmergencyService(repo)
    node = make_emergency_detection_node(agent, service)

    case_id = uuid4()
    state = create_initial_state(case_id, uuid4())

    update = await node(state)

    assert update["emergency_assessment"] == assessment
    assert await service.get_latest_assessment(case_id) is None
