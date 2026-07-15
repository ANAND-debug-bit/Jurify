"""Supervisor Agent (Module 10, Change 1).

Routes execution between graph nodes based on a condensed state summary
— never the full case narrative. This is the structural enforcement
behind "the Supervisor should never perform legal reasoning itself"
(docs/architecture/02-agent-architecture.md §2.2.4, ADR-12): its input
excludes case_profile/timeline/legal_research free text, and its output
schema (RoutingDecision) has no field capable of carrying analysis.

Validating that a chosen next_node is actually reachable from the
current call site (the `legal_targets` set in docs/architecture/03-
langgraph-workflow.md §3.5) is graph/edges.py's job once it exists
(deferred — nothing calls this agent from the graph yet, see
graph/nodes/supervisor_node.py).
"""

from __future__ import annotations

from typing import Any

from app.agents.base import BaseAgent
from app.graph.state import CaseState
from app.prompts.supervisor import build_supervisor_system_prompt
from app.schemas.routing import RoutingDecision


class SupervisorAgent(BaseAgent[RoutingDecision]):
    name = "supervisor"
    output_schema = RoutingDecision

    def _system_prompt(self) -> str:
        return build_supervisor_system_prompt()

    def _build_user_content(self, state: CaseState, context: Any) -> str:
        missing_fields = state.get("missing_fields") or []
        emergency = state.get("emergency_assessment")
        evidence_report = state.get("evidence_report")
        risk = state.get("risk_assessment")
        strategy_plan = state.get("strategy_plan")

        needs_representation = False
        if strategy_plan is not None and strategy_plan.options:
            recommended = strategy_plan.options[strategy_plan.recommended_option_index]
            needs_representation = recommended.required_specialization is not None

        lines = [
            f"status: {state['status'].value}",
            f"missing_fields: {missing_fields}",
            f"is_emergency: {emergency.is_emergency if emergency else False}",
            (
                "evidence_completeness_score: "
                f"{evidence_report.completeness_score if evidence_report else 'unknown'}"
            ),
            f"risk_case_strength: {risk.case_strength if risk else 'unknown'}",
            f"strategy_needs_representation: {needs_representation}",
            f"round_count: {state['round_count']}",
            f"max_rounds: {state['max_rounds']}",
        ]
        return "\n".join(lines)
