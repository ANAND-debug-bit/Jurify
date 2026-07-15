"""Supervisor node — thin wrapper around SupervisorAgent (Module 10).

docs/architecture/06-folder-structure.md describes this as a "thin
wrapper, see agents/supervisor_agent.py" — it only logs the node
execution and merges the routing decision back into CaseState. Not yet
wired into graph_builder.py: there is nothing to route between until
Module 11 (Intake) lands.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from app.agents.supervisor_agent import SupervisorAgent
from app.core.execution_logging import log_node_execution
from app.graph.state import CaseState


def make_supervisor_node(
    agent: SupervisorAgent,
) -> Callable[[CaseState], Awaitable[dict[str, Any]]]:
    async def supervisor_node(state: CaseState) -> dict[str, Any]:
        async with log_node_execution("supervisor"):
            result = await agent.run(state)
            return {"last_routing_decision": result.output}

    return supervisor_node
