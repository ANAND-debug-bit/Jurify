"""Evidence Analysis node — thin wrapper around EvidenceAnalysisAgent
(Module 14).

Unlike the other Module 12/13 nodes, this one loads data the agent needs
*before* calling it: `evidence_items` isn't populated by an earlier node
(evidence is submitted via its own user action, not part of the linear
state hand-off), so the node fetches it from EvidenceService and injects
it into a working copy of state (see app/graph/state.py's comment on
`evidence_items` for why this field exists at all).

Sets status to ANALYZING_EVIDENCE (self-describing "this stage ran"), not
a forward-looking status — unlike case_reconstruction_node/
legal_research_node, what happens next here is a genuine branch (pause
for more evidence, or proceed) decided by app.graph.edges.
evidence_analysis_route, not something this node should presuppose.

Also unconditionally clears `awaiting_evidence_upload` — harmless on a
first run (already False), and required on a resumed run: per
docs/architecture/03-langgraph-workflow.md §3.6, the graph resumes at
this exact node after the user uploads more evidence, and the pause flag
must not still read True once evidence is being analyzed again.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, cast

from app.agents.evidence_analysis_agent import EvidenceAnalysisAgent
from app.core.execution_logging import log_node_execution
from app.graph.state import CaseState
from app.schemas._common import CaseStatus
from app.services.evidence_service import EvidenceService


def make_evidence_analysis_node(
    agent: EvidenceAnalysisAgent, evidence_service: EvidenceService
) -> Callable[[CaseState], Awaitable[dict[str, Any]]]:
    async def evidence_analysis_node(state: CaseState) -> dict[str, Any]:
        async with log_node_execution("evidence_analysis"):
            evidence_items = await evidence_service.list_evidence(state["case_id"])
            working_state = cast(CaseState, {**state, "evidence_items": evidence_items})

            result = await agent.run(working_state)
            report = result.output
            await evidence_service.save_report(state["case_id"], report)

            return {
                "evidence_items": evidence_items,
                "evidence_report": report,
                "status": CaseStatus.ANALYZING_EVIDENCE,
                "awaiting_evidence_upload": False,
            }

    return evidence_analysis_node
