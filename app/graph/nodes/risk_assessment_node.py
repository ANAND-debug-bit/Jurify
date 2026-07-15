"""Risk Assessment node — thin wrapper around RiskAssessmentAgent
(Module 15).

Sets status to PLANNING_STRATEGY (forward-looking), unlike
evidence_analysis_node's self-describing status — RiskAssessment ->
StrategyPlanning is a fixed, unconditional edge (docs/architecture/
03-langgraph-workflow.md §3.3: "A5 --> A6", no Supervisor call in
between), so this node can safely presuppose the next stage the same way
case_reconstruction_node/legal_research_node do.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from app.agents.risk_assessment_agent import RiskAssessmentAgent
from app.core.execution_logging import log_node_execution
from app.graph.state import CaseState
from app.schemas._common import CaseStatus
from app.services.case_service import CaseService


def make_risk_assessment_node(
    agent: RiskAssessmentAgent, case_service: CaseService
) -> Callable[[CaseState], Awaitable[dict[str, Any]]]:
    async def risk_assessment_node(state: CaseState) -> dict[str, Any]:
        async with log_node_execution("risk_assessment"):
            result = await agent.run(state)
            risk = result.output
            await case_service.save_risk_score(state["case_id"], risk)
            return {"risk_assessment": risk, "status": CaseStatus.PLANNING_STRATEGY}

    return risk_assessment_node
