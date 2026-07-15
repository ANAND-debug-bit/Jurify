"""Legal Research node — thin wrapper around LegalResearchAgent
(Module 12). Advances status to VERIFYING_CITATIONS since the
Verification Agent (Module 13) is the next stage every research pass
must go through before its citations are trusted anywhere downstream.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from app.agents.legal_research_agent import LegalResearchAgent
from app.core.execution_logging import log_node_execution
from app.graph.state import CaseState
from app.schemas._common import CaseStatus
from app.services.case_service import CaseService


def make_legal_research_node(
    agent: LegalResearchAgent, case_service: CaseService
) -> Callable[[CaseState], Awaitable[dict[str, Any]]]:
    async def legal_research_node(state: CaseState) -> dict[str, Any]:
        async with log_node_execution("legal_research"):
            result = await agent.run(state)
            legal_research = result.output
            await case_service.save_legal_research(state["case_id"], legal_research)
            return {"legal_research": legal_research, "status": CaseStatus.VERIFYING_CITATIONS}

    return legal_research_node
