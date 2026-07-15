from __future__ import annotations

from uuid import uuid4

import pytest

from app.agents.emergency_agent import EmergencyAgent
from app.core.config import Settings
from app.graph.state import create_initial_state
from app.llm.gemma_client import get_chat_model
from app.schemas.emergency import (
    EmergencyAssessment,
    EmergencyCategory,
    EmergencyGuidance,
    HelplineInfo,
)
from tests.conftest import ollama_is_reachable
from tests.unit.agents.fakes import FakeStructuredChatModel


async def test_emergency_agent_returns_guidance_from_fake() -> None:
    guidance = EmergencyGuidance(
        immediate_steps=["Call 100"],
        evidence_preservation_checklist=["Photograph injuries"],
        helplines=[HelplineInfo(name="Police", phone="100", available="24x7")],
        recommended_authorities=["Nearest Police Station"],
    )
    llm = FakeStructuredChatModel(responses=[guidance])
    agent = EmergencyAgent(llm, model_name="fake-model")

    state = create_initial_state(uuid4(), uuid4())
    state["emergency_assessment"] = EmergencyAssessment(
        is_emergency=True, category=EmergencyCategory.ILLEGAL_DETENTION, severity="critical",
        rationale="user is being held against their will",
    )

    result = await agent.run(state)

    assert result.output.immediate_steps == ["Call 100"]


def test_build_user_content_includes_assessment_details() -> None:
    llm = FakeStructuredChatModel(responses=[])
    agent = EmergencyAgent(llm, model_name="fake-model")

    state = create_initial_state(uuid4(), uuid4())
    state["emergency_assessment"] = EmergencyAssessment(
        is_emergency=True, category=EmergencyCategory.KIDNAPPING, severity="critical",
        rationale="child reported missing",
    )

    content = agent._build_user_content(state, None)

    assert "kidnapping" in content
    assert "critical" in content
    assert "child reported missing" in content


def test_build_user_content_handles_missing_assessment() -> None:
    llm = FakeStructuredChatModel(responses=[])
    agent = EmergencyAgent(llm, model_name="fake-model")

    content = agent._build_user_content(create_initial_state(uuid4(), uuid4()), None)

    assert "No emergency assessment available." in content


@pytest.mark.skipif(not ollama_is_reachable(), reason="no local Ollama server reachable")
async def test_emergency_agent_live_produces_correct_indian_helplines(monkeypatch) -> None:
    monkeypatch.setenv("GEMMA_MODEL_NAME", "gemma2:2b")
    settings = Settings()
    llm = get_chat_model(settings)
    agent = EmergencyAgent(llm, model_name=settings.llm.gemma_model_name)

    state = create_initial_state(uuid4(), uuid4())
    state["emergency_assessment"] = EmergencyAssessment(
        is_emergency=True, category=EmergencyCategory.DOMESTIC_VIOLENCE, severity="high",
        rationale="user reports being locked in by husband who has hit her before",
    )

    result = await agent.run(state)

    assert result.output.immediate_steps
    assert result.output.helplines
    for helpline in result.output.helplines:
        if helpline.name.lower().startswith("police"):
            assert helpline.phone == "100"
