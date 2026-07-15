from __future__ import annotations

from uuid import uuid4

import pytest
from langchain_core.messages import HumanMessage

from app.agents.case_intake_agent import CaseIntakeAgent
from app.core.config import Settings
from app.graph.state import create_initial_state
from app.llm.gemma_client import get_chat_model
from app.schemas.case import CaseProfile
from tests.conftest import ollama_is_reachable
from tests.unit.agents.fakes import FakeStructuredChatModel


async def test_case_intake_returns_profile_from_fake() -> None:
    profile = CaseProfile(
        incident_category="consumer_dispute", summary="washing machine broke", confidence=0.7
    )
    llm = FakeStructuredChatModel(responses=[profile])
    agent = CaseIntakeAgent(llm, model_name="fake-model")

    state = create_initial_state(uuid4(), uuid4())
    state["messages"] = [HumanMessage(content="my washing machine broke")]

    result = await agent.run(state)

    assert result.output.incident_category == "consumer_dispute"


def test_build_user_content_includes_conversation_and_existing_profile() -> None:
    llm = FakeStructuredChatModel(responses=[])
    agent = CaseIntakeAgent(llm, model_name="fake-model")

    state = create_initial_state(uuid4(), uuid4())
    state["messages"] = [HumanMessage(content="the seller wont refund me")]
    state["case_profile"] = CaseProfile(
        incident_category="consumer_dispute", summary="prior summary", confidence=0.5
    )

    content = agent._build_user_content(state, None)

    assert "the seller wont refund me" in content
    assert "prior summary" in content


def test_build_user_content_handles_no_existing_profile() -> None:
    llm = FakeStructuredChatModel(responses=[])
    agent = CaseIntakeAgent(llm, model_name="fake-model")

    state = create_initial_state(uuid4(), uuid4())
    state["messages"] = [HumanMessage(content="hello")]

    content = agent._build_user_content(state, None)

    assert "null" in content


@pytest.mark.skipif(not ollama_is_reachable(), reason="no local Ollama server reachable")
async def test_case_intake_live_extracts_structured_profile(monkeypatch) -> None:
    monkeypatch.setenv("GEMMA_MODEL_NAME", "gemma2:2b")
    settings = Settings()
    llm = get_chat_model(settings)
    agent = CaseIntakeAgent(llm, model_name=settings.llm.gemma_model_name)

    state = create_initial_state(uuid4(), uuid4())
    state["messages"] = [
        HumanMessage(
            content=(
                "I bought a washing machine from ABC Electronics in Delhi last week and "
                "it stopped working after 2 days. They refuse to replace it or refund me."
            )
        )
    ]

    result = await agent.run(state)

    assert isinstance(result.output, CaseProfile)
    assert result.output.incident_category
    assert result.output.summary
    assert 0.0 <= result.output.confidence <= 1.0
