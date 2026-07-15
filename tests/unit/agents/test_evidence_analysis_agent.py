from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.agents.evidence_analysis_agent import EvidenceAnalysisAgent
from app.core.config import Settings
from app.domain.entities.evidence import Evidence
from app.graph.state import create_initial_state
from app.llm.gemma_client import get_chat_model
from app.schemas._common import UrgencyLevel
from app.schemas.case import CaseProfile
from app.schemas.evidence import EvidenceGap, EvidenceItem, EvidenceQuality, EvidenceReport
from tests.conftest import ollama_is_reachable
from tests.unit.agents.fakes import FakeStructuredChatModel


def _evidence(evidence_type: str, description: str) -> Evidence:
    return Evidence(
        id=uuid4(),
        case_id=uuid4(),
        evidence_type=evidence_type,
        description=description,
        created_at=datetime.now(UTC),
    )


async def test_returns_evidence_report_from_fake() -> None:
    output = EvidenceReport(
        submitted_evidence=[
            EvidenceItem(evidence_type="photo", description="damaged item", quality=EvidenceQuality.MODERATE)
        ],
        gaps=[
            EvidenceGap(
                description="No proof of purchase",
                suggested_evidence="Upload a receipt",
                priority=UrgencyLevel.CRITICAL,
            )
        ],
        completeness_score=40.0,
        summary="Some evidence submitted, but no proof of purchase.",
    )
    llm = FakeStructuredChatModel(responses=[output])
    agent = EvidenceAnalysisAgent(llm, model_name="fake-model")

    state = create_initial_state(uuid4(), uuid4())
    state["case_profile"] = CaseProfile(
        incident_category="consumer_dispute", summary="x", confidence=0.7
    )
    state["evidence_items"] = [_evidence("photo", "damaged item")]

    result = await agent.run(state)

    assert result.output.completeness_score == 40.0
    assert result.output.gaps[0].priority == UrgencyLevel.CRITICAL


def test_build_user_content_handles_missing_profile() -> None:
    llm = FakeStructuredChatModel(responses=[])
    agent = EvidenceAnalysisAgent(llm, model_name="fake-model")

    content = agent._build_user_content(create_initial_state(uuid4(), uuid4()), None)

    assert "No case profile available yet." in content
    assert "no evidence submitted yet" in content


def test_build_user_content_lists_submitted_evidence_verbatim() -> None:
    llm = FakeStructuredChatModel(responses=[])
    agent = EvidenceAnalysisAgent(llm, model_name="fake-model")
    state = create_initial_state(uuid4(), uuid4())
    state["case_profile"] = CaseProfile(
        incident_category="consumer_dispute", summary="x", confidence=0.7
    )
    state["evidence_items"] = [_evidence("receipt", "purchase receipt dated 2026-01-10")]

    content = agent._build_user_content(state, None)

    assert "receipt" in content
    assert "purchase receipt dated 2026-01-10" in content


@pytest.mark.skipif(not ollama_is_reachable(), reason="no local Ollama server reachable")
async def test_live_flags_critical_gap_for_missing_purchase_proof(monkeypatch) -> None:
    monkeypatch.setenv("GEMMA_MODEL_NAME", "gemma2:2b")
    settings = Settings()
    llm = get_chat_model(settings)
    agent = EvidenceAnalysisAgent(llm, model_name=settings.llm.gemma_model_name)

    state = create_initial_state(uuid4(), uuid4())
    state["case_profile"] = CaseProfile(
        incident_category="consumer_dispute",
        summary="Bought a washing machine that broke after two days; seller refuses a refund.",
        confidence=0.8,
    )
    state["evidence_items"] = [
        _evidence("photo", "Photo of the broken washing machine, no receipt or invoice submitted")
    ]

    result = await agent.run(state)

    assert len(result.output.submitted_evidence) >= 1
    assert 0.0 <= result.output.completeness_score <= 100.0
