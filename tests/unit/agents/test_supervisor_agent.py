from __future__ import annotations

from uuid import uuid4

import pytest

from app.agents.supervisor_agent import SupervisorAgent
from app.core.config import Settings
from app.graph.state import create_initial_state
from app.llm.gemma_client import get_chat_model
from app.schemas._common import CaseStatus
from app.schemas.evidence import EvidenceReport
from app.schemas.routing import NodeName, RoutingDecision
from tests.conftest import ollama_is_reachable
from tests.unit.agents.fakes import FakeStructuredChatModel


async def test_supervisor_returns_routing_decision_from_fake() -> None:
    decision = RoutingDecision(
        next_node=NodeName.CASE_RECONSTRUCTION, reason="intake complete"
    )
    llm = FakeStructuredChatModel(responses=[decision])
    agent = SupervisorAgent(llm, model_name="fake-model")

    state = create_initial_state(uuid4(), uuid4())
    result = await agent.run(state)

    assert result.output.next_node == NodeName.CASE_RECONSTRUCTION
    assert result.success is True


def test_build_user_content_never_includes_case_profile_text() -> None:
    llm = FakeStructuredChatModel(responses=[])
    agent = SupervisorAgent(llm, model_name="fake-model")

    state = create_initial_state(uuid4(), uuid4())
    state["evidence_report"] = EvidenceReport(
        submitted_evidence=[], gaps=[], completeness_score=42.0, summary="a secret narrative"
    )

    content = agent._build_user_content(state, None)

    # The condensed score is present, but the free-text summary is not —
    # this is the structural enforcement behind ADR-12.
    assert "42.0" in content
    assert "secret narrative" not in content


def test_build_user_content_reports_missing_fields() -> None:
    llm = FakeStructuredChatModel(responses=[])
    agent = SupervisorAgent(llm, model_name="fake-model")

    state = create_initial_state(uuid4(), uuid4())
    state["missing_fields"] = ["incident_date", "location"]

    content = agent._build_user_content(state, None)

    assert "incident_date" in content
    assert "location" in content


@pytest.mark.skipif(not ollama_is_reachable(), reason="no local Ollama server reachable")
async def test_supervisor_live_routes_intake_with_missing_fields(monkeypatch) -> None:
    monkeypatch.setenv("GEMMA_MODEL_NAME", "gemma2:2b")
    settings = Settings()
    llm = get_chat_model(settings)
    agent = SupervisorAgent(llm, model_name=settings.llm.gemma_model_name)

    state = create_initial_state(uuid4(), uuid4())
    state["status"] = CaseStatus.INTAKE_IN_PROGRESS
    state["missing_fields"] = ["incident_date", "location"]

    result = await agent.run(state)

    assert isinstance(result.output, RoutingDecision)
    assert result.output.next_node in set(NodeName)
    assert result.output.reason


@pytest.mark.skipif(not ollama_is_reachable(), reason="no local Ollama server reachable")
async def test_supervisor_live_routes_forward_when_intake_complete(monkeypatch) -> None:
    monkeypatch.setenv("GEMMA_MODEL_NAME", "gemma2:2b")
    settings = Settings()
    llm = get_chat_model(settings)
    agent = SupervisorAgent(llm, model_name=settings.llm.gemma_model_name)

    state = create_initial_state(uuid4(), uuid4())
    state["status"] = CaseStatus.INTAKE_COMPLETE
    state["missing_fields"] = []

    result = await agent.run(state)

    assert isinstance(result.output, RoutingDecision)
