from __future__ import annotations

from uuid import uuid4

import pytest

from app.agents.risk_assessment_agent import RiskAssessmentAgent
from app.core.config import Settings
from app.graph.state import create_initial_state
from app.llm.gemma_client import get_chat_model
from app.schemas.case import CaseProfile
from app.schemas.risk import RiskAssessment
from tests.conftest import ollama_is_reachable
from tests.unit.agents.fakes import FakeStructuredChatModel


async def test_returns_risk_assessment_from_fake() -> None:
    output = RiskAssessment(
        financial_risk=30.0,
        criminal_risk=0.0,
        urgency="medium",
        needs_police=False,
        needs_lawyer=True,
        needs_medical=False,
        settlement_probability=60.0,
        case_strength=55.0,
        rationale="Consumer dispute with moderate evidence.",
    )
    llm = FakeStructuredChatModel(responses=[output])
    agent = RiskAssessmentAgent(llm, model_name="fake-model")

    state = create_initial_state(uuid4(), uuid4())
    state["case_profile"] = CaseProfile(
        incident_category="consumer_dispute", summary="x", confidence=0.7
    )

    result = await agent.run(state)

    assert result.output.case_strength == 55.0
    assert result.output.needs_lawyer is True


def test_build_user_content_handles_missing_profile() -> None:
    llm = FakeStructuredChatModel(responses=[])
    agent = RiskAssessmentAgent(llm, model_name="fake-model")

    content = agent._build_user_content(create_initial_state(uuid4(), uuid4()), None)

    assert content == "No case profile available yet."


def test_build_user_content_includes_all_four_inputs() -> None:
    llm = FakeStructuredChatModel(responses=[])
    agent = RiskAssessmentAgent(llm, model_name="fake-model")
    state = create_initial_state(uuid4(), uuid4())
    state["case_profile"] = CaseProfile(
        incident_category="consumer_dispute", summary="x", confidence=0.7
    )

    content = agent._build_user_content(state, None)

    assert "Case profile:" in content
    assert "Case timeline" in content
    assert "Verified legal research" in content
    assert "Evidence report" in content


@pytest.mark.skipif(not ollama_is_reachable(), reason="no local Ollama server reachable")
async def test_live_scores_a_consumer_dispute(monkeypatch) -> None:
    monkeypatch.setenv("GEMMA_MODEL_NAME", "gemma2:2b")
    settings = Settings()
    llm = get_chat_model(settings)
    agent = RiskAssessmentAgent(llm, model_name=settings.llm.gemma_model_name)

    state = create_initial_state(uuid4(), uuid4())
    state["case_profile"] = CaseProfile(
        incident_category="consumer_dispute",
        summary=(
            "Bought a washing machine that broke after two days; seller refuses a refund "
            "despite a valid purchase receipt being available."
        ),
        confidence=0.8,
    )

    result = await agent.run(state)

    assert 0.0 <= result.output.case_strength <= 100.0
    assert result.output.criminal_risk == 0.0
    assert result.output.rationale
