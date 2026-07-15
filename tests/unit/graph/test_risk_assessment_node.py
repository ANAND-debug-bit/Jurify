from __future__ import annotations

from uuid import uuid4

from app.agents.risk_assessment_agent import RiskAssessmentAgent
from app.graph.nodes.risk_assessment_node import make_risk_assessment_node
from app.graph.state import create_initial_state
from app.schemas._common import CaseStatus
from app.schemas.language import SupportedLanguage
from app.schemas.risk import RiskAssessment
from app.services.case_service import CaseService
from tests.unit.agents.fakes import FakeStructuredChatModel
from tests.unit.services.fakes import FakeCaseRepository, FakeEvidenceRepository


async def test_node_saves_risk_score_and_advances_status() -> None:
    risk = RiskAssessment(
        financial_risk=20.0,
        criminal_risk=0.0,
        urgency="medium",
        needs_police=False,
        needs_lawyer=True,
        needs_medical=False,
        settlement_probability=50.0,
        case_strength=60.0,
        rationale="x",
    )
    llm = FakeStructuredChatModel(responses=[risk])
    agent = RiskAssessmentAgent(llm, model_name="fake-model")
    case_repo = FakeCaseRepository()
    service = CaseService(case_repo, FakeEvidenceRepository())
    node = make_risk_assessment_node(agent, service)

    case = await case_repo.create(uuid4(), SupportedLanguage.EN)
    state = create_initial_state(case.id, uuid4())

    update = await node(state)

    assert update["status"] == CaseStatus.PLANNING_STRATEGY
    assert update["risk_assessment"] == risk

    saved = await service.get_latest_risk_score(case.id)
    assert saved is not None
    assert saved.case_strength == 60.0
    assert saved.rationale == "x"
