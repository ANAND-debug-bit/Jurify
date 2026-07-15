from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.routing import NodeName, RoutingDecision


def test_routing_decision_field_set_cannot_carry_legal_reasoning() -> None:
    # Structural enforcement behind ADR-12: the Supervisor's output type
    # has no field capable of expressing case analysis — only these three.
    assert set(RoutingDecision.model_fields.keys()) == {"next_node", "reason", "needs_user_input"}


def test_routing_decision_needs_user_input_defaults_false() -> None:
    decision = RoutingDecision(next_node=NodeName.CASE_RECONSTRUCTION, reason="intake complete")
    assert decision.needs_user_input is False


def test_routing_decision_rejects_node_name_outside_the_closed_set() -> None:
    with pytest.raises(ValidationError):
        RoutingDecision(next_node="some_made_up_node", reason="x")


def test_routing_decision_rejects_extra_field_like_case_analysis() -> None:
    with pytest.raises(ValidationError):
        RoutingDecision(
            next_node=NodeName.RISK_ASSESSMENT,
            reason="x",
            case_profile={"summary": "leaking through"},  # type: ignore[call-arg]
        )


def test_node_name_covers_every_graph_stage() -> None:
    expected = {
        "case_intake",
        "case_reconstruction",
        "legal_research",
        "evidence_analysis",
        "awaiting_evidence_upload",
        "risk_assessment",
        "strategy_planning",
        "government_scheme_agent",
        "lawyer_recommendation",
        "complaint_generation",
        "explainability_agent",
        "finalize_dashboard",
    }
    assert {n.value for n in NodeName} == expected
