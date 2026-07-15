"""awaiting_evidence_upload node — Change 7's pause point (Module 14,
docs/architecture/03-langgraph-workflow.md §3.6).

Deliberately does no LLM work: its entire job is to mark the case paused
and persist that fact. Checkpointing and "returning control" happen
because this is a terminal node for this graph invocation (nothing
downstream is wired to run after it in the same call) — `POST
/case/evidence` is what eventually resumes the case by re-invoking the
graph starting at evidence_analysis, per that section's step 3. That
endpoint doesn't exist yet (Module 24+); this node is the piece of the
mechanism Module 14 owns.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from app.core.execution_logging import log_node_execution
from app.graph.state import CaseState
from app.schemas._common import CaseStatus
from app.services.case_service import CaseService


def make_awaiting_evidence_upload_node(
    case_service: CaseService,
) -> Callable[[CaseState], Awaitable[dict[str, Any]]]:
    async def awaiting_evidence_upload_node(state: CaseState) -> dict[str, Any]:
        async with log_node_execution("awaiting_evidence_upload"):
            new_pause_count = state["evidence_pause_count"] + 1
            await case_service.set_evidence_pause_state(
                state["case_id"],
                awaiting_evidence_upload=True,
                evidence_pause_count=new_pause_count,
            )
            return {
                "status": CaseStatus.AWAITING_EVIDENCE_UPLOAD,
                "awaiting_evidence_upload": True,
                "evidence_pause_count": new_pause_count,
            }

    return awaiting_evidence_upload_node
