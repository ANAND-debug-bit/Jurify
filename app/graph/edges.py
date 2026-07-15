"""Graph-level conditional routing functions (Module 13, extended
Module 14).

Distinct from Supervisor-driven routing (SupervisorAgent's
RoutingDecision) — these are FIXED conditional edges encoded directly by
the graph author per docs/architecture/03-langgraph-workflow.md §3.3, not
agent decisions. Both routing functions here are deliberately not yet
wired into graph_builder.py (see that file's docstring): the graph can't
be compiled until the pipeline stages after Evidence Analysis (Risk
Assessment onward, Module 15+) exist to route to, so each is unit-tested
directly against a CaseState rather than through a compiled graph for
now.
"""

from __future__ import annotations

from app.graph.state import CaseState
from app.schemas._common import UrgencyLevel

LEGAL_RESEARCH = "legal_research"
SUPERVISOR_2 = "supervisor_2"
AWAITING_EVIDENCE_UPLOAD = "awaiting_evidence_upload"
RISK_ASSESSMENT = "risk_assessment"

MAX_VERIFICATION_RETRIES = 1
MAX_EVIDENCE_PAUSES = 2


def verification_route(state: CaseState) -> str:
    """docs/architecture/03-langgraph-workflow.md §3.3: "VerificationAgent
    --> LegalResearch: too many rejected citations (bounded: 1 retry)".

    "Too many rejected" is defined here as: at least one citation was not
    verified, and verified citations don't outnumber the rejected/
    unverified ones — the research pass came back majority-unusable. A
    single stray rejected citation alongside several verified ones is not
    grounds to re-run the whole research step. A pass with zero citations
    either way (nothing claimed, nothing rejected) is not a verification
    failure to retry — it means Legal Research found nothing to cite,
    which re-running Legal Research is unlikely to fix.

    `verification_retry_count` is incremented by verification_node on
    every run (not by this function — routing functions stay read-only),
    so this checks the count *before* the run that just produced
    `verified_legal_research` counts as the retry itself.
    """
    verified = state["verified_legal_research"]
    if verified is None:
        # Should never happen — verification_node always sets this field
        # — but fail toward re-running research rather than silently
        # proceeding with nothing to show the user.
        return LEGAL_RESEARCH

    verified_count = sum(len(provision.citations) for provision in verified.verified_provisions)
    rejected_count = len(verified.rejected_citations)
    too_many_rejected = rejected_count > 0 and rejected_count >= verified_count

    if too_many_rejected and state["verification_retry_count"] <= MAX_VERIFICATION_RETRIES:
        return LEGAL_RESEARCH
    return SUPERVISOR_2


def evidence_analysis_route(state: CaseState) -> str:
    """docs/architecture/03-langgraph-workflow.md §3.6: pause for more
    evidence when `EvidenceReport.gaps` contains a priority=CRITICAL
    item, bounded to 2 pause/resume cycles — "after 2 pause/resume cycles
    without reaching an acceptable completeness score... proceed to
    risk_assessment regardless... the case proceeds with a documented
    evidence gap rather than looping indefinitely."

    `evidence_pause_count` is incremented by awaiting_evidence_upload_node
    only when it actually runs (not by this function), so a case that has
    paused twice already (count == 2) does not pause a third time even if
    another critical gap remains.
    """
    report = state["evidence_report"]
    if report is None:
        # Should never happen — evidence_analysis_node always sets this
        # field — but proceeding is safer than pausing on a phantom gap
        # with nothing to show the user why.
        return RISK_ASSESSMENT

    has_critical_gap = any(gap.priority == UrgencyLevel.CRITICAL for gap in report.gaps)
    if has_critical_gap and state["evidence_pause_count"] < MAX_EVIDENCE_PAUSES:
        return AWAITING_EVIDENCE_UPLOAD
    return RISK_ASSESSMENT
