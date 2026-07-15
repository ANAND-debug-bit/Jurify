from __future__ import annotations

from uuid import uuid4

from app.agents.emergency_agent import EmergencyAgent
from app.graph.nodes.emergency_agent_node import make_emergency_agent_node
from app.graph.state import create_initial_state
from app.schemas.emergency import (
    EmergencyAssessment,
    EmergencyCategory,
    EmergencyGuidance,
    HelplineInfo,
)
from app.services.emergency_service import EmergencyService
from tests.unit.agents.fakes import FakeStructuredChatModel
from tests.unit.services.fakes import FakeEmergencyRepository


async def test_node_persists_combined_assessment_and_guidance() -> None:
    guidance = EmergencyGuidance(
        immediate_steps=["Call 100"],
        evidence_preservation_checklist=["Photograph injuries"],
        helplines=[HelplineInfo(name="Police", phone="100", available="24x7")],
        recommended_authorities=["Nearest Police Station"],
    )
    llm = FakeStructuredChatModel(responses=[guidance])
    agent = EmergencyAgent(llm, model_name="fake-model")
    repo = FakeEmergencyRepository()
    service = EmergencyService(repo)
    node = make_emergency_agent_node(agent, service)

    case_id = uuid4()
    state = create_initial_state(case_id, uuid4())
    state["emergency_assessment"] = EmergencyAssessment(
        is_emergency=True, category=EmergencyCategory.DOMESTIC_VIOLENCE, severity="high",
        rationale="ongoing abuse reported",
    )

    update = await node(state)

    assert update["emergency_guidance"] == guidance
    latest = await service.get_latest_assessment(case_id)
    assert latest is not None
    assert latest.is_emergency is True
    assert latest.immediate_steps == ["Call 100"]


async def test_node_skips_persistence_when_no_assessment_in_state() -> None:
    guidance = EmergencyGuidance(
        immediate_steps=[], evidence_preservation_checklist=[], helplines=[],
        recommended_authorities=[],
    )
    llm = FakeStructuredChatModel(responses=[guidance])
    agent = EmergencyAgent(llm, model_name="fake-model")
    repo = FakeEmergencyRepository()
    service = EmergencyService(repo)
    node = make_emergency_agent_node(agent, service)

    case_id = uuid4()
    state = create_initial_state(case_id, uuid4())

    await node(state)

    assert await service.get_latest_assessment(case_id) is None
