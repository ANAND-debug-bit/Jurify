"""Emergency Detection node (Module 11, Change 4).

Persists the assessment ONLY when no emergency was found — if
is_emergency is true, emergency_agent_node persists the COMBINED
assessment+guidance row instead, so exactly one row is written per
intake turn (docs/architecture/04-database-design.md §4.2: append-only,
one row per turn, holding both agents' outputs).
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from app.agents.emergency_detection_agent import EmergencyDetectionAgent
from app.core.execution_logging import log_node_execution
from app.graph.state import CaseState
from app.services.emergency_service import EmergencyService


def make_emergency_detection_node(
    agent: EmergencyDetectionAgent, emergency_service: EmergencyService
) -> Callable[[CaseState], Awaitable[dict[str, Any]]]:
    async def emergency_detection_node(state: CaseState) -> dict[str, Any]:
        async with log_node_execution("emergency_detection"):
            result = await agent.run(state)
            assessment = result.output
            if not assessment.is_emergency:
                await emergency_service.record_assessment(state["case_id"], assessment)
            return {"emergency_assessment": assessment}

    return emergency_detection_node
