from __future__ import annotations

from uuid import uuid4

from app.agents.evidence_analysis_agent import EvidenceAnalysisAgent
from app.domain.entities.evidence import EvidenceSubmission
from app.graph.nodes.evidence_analysis_node import make_evidence_analysis_node
from app.graph.state import create_initial_state
from app.schemas._common import CaseStatus, UrgencyLevel
from app.schemas.evidence import EvidenceGap, EvidenceItem, EvidenceQuality, EvidenceReport
from app.schemas.language import SupportedLanguage
from app.services.evidence_service import EvidenceService
from tests.unit.agents.fakes import FakeStructuredChatModel
from tests.unit.services.fakes import FakeCaseRepository, FakeEvidenceRepository


async def test_node_loads_evidence_saves_report_and_sets_status() -> None:
    output = EvidenceReport(
        submitted_evidence=[
            EvidenceItem(evidence_type="photo", description="x", quality=EvidenceQuality.WEAK)
        ],
        gaps=[
            EvidenceGap(
                description="missing receipt",
                suggested_evidence="upload receipt",
                priority=UrgencyLevel.CRITICAL,
            )
        ],
        completeness_score=25.0,
        summary="early stage",
    )
    llm = FakeStructuredChatModel(responses=[output])
    agent = EvidenceAnalysisAgent(llm, model_name="fake-model")
    case_repo = FakeCaseRepository()
    evidence_repo = FakeEvidenceRepository()
    evidence_service = EvidenceService(evidence_repo)
    node = make_evidence_analysis_node(agent, evidence_service)

    case = await case_repo.create(uuid4(), SupportedLanguage.EN)
    await evidence_service.submit_evidence(
        case.id, [EvidenceSubmission(evidence_type="photo", description="x")]
    )
    state = create_initial_state(case.id, uuid4())

    update = await node(state)

    assert update["status"] == CaseStatus.ANALYZING_EVIDENCE
    assert len(update["evidence_items"]) == 1
    assert update["evidence_report"].completeness_score == 25.0

    saved = await evidence_service.get_latest_report(case.id)
    assert saved is not None
    assert saved.summary == "early stage"


async def test_node_handles_no_submitted_evidence() -> None:
    output = EvidenceReport(
        submitted_evidence=[], gaps=[], completeness_score=0.0, summary="nothing submitted yet"
    )
    llm = FakeStructuredChatModel(responses=[output])
    agent = EvidenceAnalysisAgent(llm, model_name="fake-model")
    case_repo = FakeCaseRepository()
    evidence_service = EvidenceService(FakeEvidenceRepository())
    node = make_evidence_analysis_node(agent, evidence_service)

    case = await case_repo.create(uuid4(), SupportedLanguage.EN)
    state = create_initial_state(case.id, uuid4())

    update = await node(state)

    assert update["evidence_items"] == []
    assert update["evidence_report"].summary == "nothing submitted yet"
