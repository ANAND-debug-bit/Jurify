"""Emergency Agent node (Module 11, Change 4).

Persists the combined assessment+guidance row — see
emergency_detection_node.py for why persistence is split across the two
nodes this way.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from app.agents.emergency_agent import EmergencyAgent
from app.core.execution_logging import log_node_execution
from app.graph.state import CaseState
from app.services.emergency_service import EmergencyService


def make_emergency_agent_node(
    agent: EmergencyAgent, emergency_service: EmergencyService
) -> Callable[[CaseState], Awaitable[dict[str, Any]]]:
    async def emergency_agent_node(state: CaseState) -> dict[str, Any]:
        async with log_node_execution("emergency_agent"):
            result = await agent.run(state)
            guidance = result.output
            assessment = state.get("emergency_assessment")
            if assessment is not None:
                await emergency_service.record_assessment(
                    state["case_id"], assessment, guidance
                )
            return {"emergency_guidance": guidance}

    return emergency_agent_node
