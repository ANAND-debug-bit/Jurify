"""Case Intake node — thin wrapper around CaseIntakeAgent (Module 11).

Persists the updated CaseProfile via IntakeService and updates
CaseState.status based on whether required fields are still missing —
this status/missing_fields pair is what the Supervisor reads to decide
whether to loop back to case_intake or proceed
(docs/architecture/03-langgraph-workflow.md §3.3, §3.5).
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from app.agents.case_intake_agent import CaseIntakeAgent
from app.core.execution_logging import log_node_execution
from app.graph.state import CaseState
from app.schemas._common import CaseStatus
from app.services.intake_service import IntakeService


def make_case_intake_node(
    agent: CaseIntakeAgent, intake_service: IntakeService
) -> Callable[[CaseState], Awaitable[dict[str, Any]]]:
    async def case_intake_node(state: CaseState) -> dict[str, Any]:
        async with log_node_execution("case_intake"):
            result = await agent.run(state)
            profile = result.output
            await intake_service.save_profile(state["case_id"], profile)

            status = (
                CaseStatus.INTAKE_COMPLETE
                if not profile.missing_fields
                else CaseStatus.INTAKE_IN_PROGRESS
            )
            return {
                "case_profile": profile,
                "missing_fields": profile.missing_fields,
                "status": status,
            }

    return case_intake_node
