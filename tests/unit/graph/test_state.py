from __future__ import annotations

from uuid import uuid4

from app.graph.state import DEFAULT_MAX_ROUNDS, CaseState, create_initial_state
from app.schemas._common import CaseStatus
from app.schemas.language import SupportedLanguage


def test_create_initial_state_has_every_expected_key() -> None:
    state = create_initial_state(uuid4(), uuid4())

    assert set(state.keys()) == set(CaseState.__annotations__.keys())


def test_create_initial_state_defaults() -> None:
    case_id = uuid4()
    user_id = uuid4()

    state = create_initial_state(case_id, user_id)

    assert state["case_id"] == case_id
    assert state["user_id"] == user_id
    assert state["status"] == CaseStatus.INTAKE_IN_PROGRESS
    assert state["language"] == SupportedLanguage.EN
    assert state["max_rounds"] == DEFAULT_MAX_ROUNDS
    assert state["round_count"] == 0
    assert state["stress_test_requested"] is False
    assert state["awaiting_evidence_upload"] is False
    assert state["documents"] == []
    assert state["lawyer_matches"] == []
    assert state["opposition_rounds"] == []
    assert state["messages"] == []
    assert state["case_profile"] is None
    assert state["judge_opinion"] is None


def test_create_initial_state_respects_language_and_max_rounds_overrides() -> None:
    state = create_initial_state(uuid4(), uuid4(), language=SupportedLanguage.TA, max_rounds=5)

    assert state["language"] == SupportedLanguage.TA
    assert state["max_rounds"] == 5


def test_case_state_is_mutable_like_a_normal_dict() -> None:
    state = create_initial_state(uuid4(), uuid4())

    state["status"] = CaseStatus.RECONSTRUCTING
    state["missing_fields"].append("incident_date")

    assert state["status"] == CaseStatus.RECONSTRUCTING
    assert state["missing_fields"] == ["incident_date"]
