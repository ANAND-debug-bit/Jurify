from __future__ import annotations

from uuid import uuid4

from app.agents.case_intake_agent import CaseIntakeAgent
from app.graph.nodes.case_intake_node import make_case_intake_node
from app.graph.state import create_initial_state
from app.schemas._common import CaseStatus
from app.schemas.case import CaseProfile
from app.schemas.language import SupportedLanguage
from app.services.intake_service import IntakeService
from tests.unit.agents.fakes import FakeStructuredChatModel
from tests.unit.services.fakes import FakeCaseRepository, FakeMemoryRepository


async def test_node_saves_profile_and_marks_complete_when_no_missing_fields() -> None:
    profile = CaseProfile(
        incident_category="consumer_dispute", summary="x", confidence=0.9, missing_fields=[]
    )
    llm = FakeStructuredChatModel(responses=[profile])
    agent = CaseIntakeAgent(llm, model_name="fake-model")
    case_repo = FakeCaseRepository()
    service = IntakeService(case_repo, FakeMemoryRepository())
    node = make_case_intake_node(agent, service)

    case = await case_repo.create(uuid4(), SupportedLanguage.EN)
    state = create_initial_state(case.id, uuid4())

    update = await node(state)

    assert update["status"] == CaseStatus.INTAKE_COMPLETE
    assert update["missing_fields"] == []
    saved = await case_repo.get(case.id)
    assert saved is not None
    assert saved.case_profile is not None
    assert saved.case_profile.incident_category == "consumer_dispute"


async def test_node_marks_in_progress_when_fields_missing() -> None:
    profile = CaseProfile(
        incident_category="consumer_dispute",
        summary="x",
        confidence=0.4,
        missing_fields=["incident_date"],
    )
    llm = FakeStructuredChatModel(responses=[profile])
    agent = CaseIntakeAgent(llm, model_name="fake-model")
    case_repo = FakeCaseRepository()
    service = IntakeService(case_repo, FakeMemoryRepository())
    node = make_case_intake_node(agent, service)

    from app.schemas.language import SupportedLanguage

    case = await case_repo.create(uuid4(), SupportedLanguage.EN)
    state = create_initial_state(case.id, uuid4())

    update = await node(state)

    assert update["status"] == CaseStatus.INTAKE_IN_PROGRESS
    assert update["missing_fields"] == ["incident_date"]
