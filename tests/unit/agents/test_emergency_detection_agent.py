from __future__ import annotations

from uuid import uuid4

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from app.agents.emergency_detection_agent import EmergencyDetectionAgent
from app.core.config import Settings
from app.graph.state import create_initial_state
from app.llm.gemma_client import get_chat_model
from app.schemas.emergency import EmergencyAssessment, EmergencyCategory
from tests.conftest import ollama_is_reachable
from tests.unit.agents.fakes import FakeStructuredChatModel


async def test_emergency_detection_returns_assessment_from_fake() -> None:
    assessment = EmergencyAssessment(
        is_emergency=False, category=EmergencyCategory.NONE, severity="low", rationale="routine"
    )
    llm = FakeStructuredChatModel(responses=[assessment])
    agent = EmergencyDetectionAgent(llm, model_name="fake-model")

    state = create_initial_state(uuid4(), uuid4())
    state["messages"] = [HumanMessage(content="my washing machine broke")]

    result = await agent.run(state)

    assert result.output.is_emergency is False


def test_build_user_content_uses_only_latest_human_message() -> None:
    llm = FakeStructuredChatModel(responses=[])
    agent = EmergencyDetectionAgent(llm, model_name="fake-model")

    state = create_initial_state(uuid4(), uuid4())
    state["messages"] = [
        HumanMessage(content="first message with secret prior context"),
        AIMessage(content="assistant reply"),
        HumanMessage(content="second and latest message"),
    ]

    content = agent._build_user_content(state, None)

    assert "second and latest message" in content
    assert "secret prior context" not in content


@pytest.mark.skipif(not ollama_is_reachable(), reason="no local Ollama server reachable")
async def test_emergency_detection_live_flags_genuine_emergency(monkeypatch) -> None:
    monkeypatch.setenv("GEMMA_MODEL_NAME", "gemma2:2b")
    settings = Settings()
    llm = get_chat_model(settings)
    agent = EmergencyDetectionAgent(llm, model_name=settings.llm.gemma_model_name)

    state = create_initial_state(uuid4(), uuid4())
    state["messages"] = [
        HumanMessage(
            content=(
                "My husband locked me in the house and won't let me leave, he hit me "
                "yesterday and I am scared he will do it again tonight"
            )
        )
    ]

    result = await agent.run(state)

    assert result.output.is_emergency is True
    assert result.output.category == EmergencyCategory.DOMESTIC_VIOLENCE


@pytest.mark.skipif(not ollama_is_reachable(), reason="no local Ollama server reachable")
async def test_emergency_detection_live_does_not_flag_routine_dispute(monkeypatch) -> None:
    monkeypatch.setenv("GEMMA_MODEL_NAME", "gemma2:2b")
    settings = Settings()
    llm = get_chat_model(settings)
    agent = EmergencyDetectionAgent(llm, model_name=settings.llm.gemma_model_name)

    state = create_initial_state(uuid4(), uuid4())
    state["messages"] = [HumanMessage(content="My landlord won't return my rental deposit.")]

    result = await agent.run(state)

    assert result.output.is_emergency is False
