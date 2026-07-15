"""Case Reconstruction node — thin wrapper around CaseReconstructionAgent
(Module 12, gap-fill)."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from app.agents.case_reconstruction_agent import CaseReconstructionAgent
from app.core.execution_logging import log_node_execution
from app.graph.state import CaseState
from app.schemas._common import CaseStatus
from app.services.case_service import CaseService


def make_case_reconstruction_node(
    agent: CaseReconstructionAgent, case_service: CaseService
) -> Callable[[CaseState], Awaitable[dict[str, Any]]]:
    async def case_reconstruction_node(state: CaseState) -> dict[str, Any]:
        async with log_node_execution("case_reconstruction"):
            result = await agent.run(state)
            timeline = result.output
            await case_service.save_timeline(state["case_id"], timeline)
            return {"timeline": timeline, "status": CaseStatus.RESEARCHING}

    return case_reconstruction_node
