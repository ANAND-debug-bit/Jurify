from __future__ import annotations

from uuid import uuid4

import pytest

from app.agents.case_reconstruction_agent import CaseReconstructionAgent
from app.core.config import Settings
from app.graph.state import create_initial_state
from app.llm.gemma_client import get_chat_model
from app.schemas.case import CaseProfile
from app.schemas.timeline import Timeline, TimelineEvent
from tests.conftest import ollama_is_reachable
from tests.unit.agents.fakes import FakeStructuredChatModel


async def test_returns_timeline_from_fake() -> None:
    timeline = Timeline(
        events=[TimelineEvent(description="event 1", sequence_order=1)],
        reconstructed_summary="summary",
    )
    llm = FakeStructuredChatModel(responses=[timeline])
    agent = CaseReconstructionAgent(llm, model_name="fake-model")

    state = create_initial_state(uuid4(), uuid4())
    state["case_profile"] = CaseProfile(
        incident_category="consumer_dispute", summary="x", confidence=0.7
    )

    result = await agent.run(state)

    assert result.output.events[0].description == "event 1"


def test_build_user_content_handles_missing_profile() -> None:
    llm = FakeStructuredChatModel(responses=[])
    agent = CaseReconstructionAgent(llm, model_name="fake-model")

    content = agent._build_user_content(create_initial_state(uuid4(), uuid4()), None)

    assert "No case profile available yet." in content


@pytest.mark.skipif(not ollama_is_reachable(), reason="no local Ollama server reachable")
async def test_live_builds_chronological_timeline(monkeypatch) -> None:
    monkeypatch.setenv("GEMMA_MODEL_NAME", "gemma2:2b")
    settings = Settings()
    llm = get_chat_model(settings)
    agent = CaseReconstructionAgent(llm, model_name=settings.llm.gemma_model_name)

    state = create_initial_state(uuid4(), uuid4())
    state["case_profile"] = CaseProfile(
        incident_category="consumer_dispute",
        summary=(
            "Bought washing machine on 2026-01-10, it stopped working on 2026-01-12, "
            "seller refused refund on 2026-01-15"
        ),
        facts_collected={
            "purchase_date": "2026-01-10",
            "failure_date": "2026-01-12",
            "refusal_date": "2026-01-15",
        },
        confidence=0.8,
    )

    result = await agent.run(state)

    assert len(result.output.events) >= 1
    orders = [e.sequence_order for e in result.output.events]
    assert orders == sorted(orders)
