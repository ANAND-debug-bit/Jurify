"""Verification node — thin wrapper around VerificationAgent (Module 13).

Persists per-citation verification flags onto the `legal_citations` rows
belonging to the case's latest legal research pass (docs/architecture/
02-agent-architecture.md: "Writes verification flags onto
legal_citations"). Also tracks how many times verification has run for
this pipeline pass, via `verification_retry_count` — a pure counter, not
a routing decision; the bounded-retry decision itself (docs/architecture/
03-langgraph-workflow.md §3.3: "too many rejected citations, bounded: 1
retry") lives in app.graph.edges.verification_route, which reads this
counter rather than the node deciding its own successor.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from app.agents.verification_agent import VerificationAgent
from app.core.execution_logging import log_node_execution
from app.graph.state import CaseState
from app.schemas.verification import (
    CitationVerification,
    VerificationStatus,
    VerifiedLegalResearchResult,
)
from app.services.case_service import CaseService

_VERIFIED_NOTE = "Verified: matched independently retrieved statute evidence."


def _build_citation_verifications(
    verified: VerifiedLegalResearchResult,
) -> list[CitationVerification]:
    verifications = [
        CitationVerification(
            citation=citation, status=VerificationStatus.VERIFIED, verification_notes=_VERIFIED_NOTE
        )
        for provision in verified.verified_provisions
        for citation in provision.citations
    ]
    verifications.extend(verified.rejected_citations)
    return verifications


def make_verification_node(
    agent: VerificationAgent, case_service: CaseService
) -> Callable[[CaseState], Awaitable[dict[str, Any]]]:
    async def verification_node(state: CaseState) -> dict[str, Any]:
        async with log_node_execution("verification"):
            result = await agent.run(state)
            verified = result.output

            latest_research = await case_service.get_latest_legal_research(state["case_id"])
            if latest_research is not None:
                await case_service.save_citation_verifications(
                    latest_research.id, _build_citation_verifications(verified)
                )

            return {
                "verified_legal_research": verified,
                "verification_retry_count": state["verification_retry_count"] + 1,
            }

    return verification_node
