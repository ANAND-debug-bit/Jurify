from __future__ import annotations

from uuid import uuid4

from app.graph.edges import (
    AWAITING_EVIDENCE_UPLOAD,
    LEGAL_RESEARCH,
    RISK_ASSESSMENT,
    SUPERVISOR_2,
    evidence_analysis_route,
    verification_route,
)
from app.graph.state import create_initial_state
from app.schemas._common import UrgencyLevel
from app.schemas.evidence import EvidenceGap, EvidenceReport
from app.schemas.legal_research import LegalCitation, LegalProvision
from app.schemas.verification import (
    CitationVerification,
    VerificationStatus,
    VerifiedLegalResearchResult,
)


def _state_with(
    verified_provisions: list[LegalProvision],
    rejected_citations: list[CitationVerification],
    retry_count: int,
):
    state = create_initial_state(uuid4(), uuid4())
    state["verified_legal_research"] = VerifiedLegalResearchResult(
        jurisdiction="India",
        verified_provisions=verified_provisions,
        rejected_citations=rejected_citations,
        verification_summary="x",
    )
    state["verification_retry_count"] = retry_count
    return state


def _provision(act_name: str, section: str) -> LegalProvision:
    return LegalProvision(
        title="x",
        plain_explanation="x",
        citations=[LegalCitation(act_name=act_name, section=section)],
    )


def _rejected(act_name: str, section: str) -> CitationVerification:
    return CitationVerification(
        citation=LegalCitation(act_name=act_name, section=section),
        status=VerificationStatus.REJECTED,
        verification_notes="x",
    )


def test_routes_back_to_legal_research_when_majority_rejected_on_first_pass() -> None:
    state = _state_with(
        verified_provisions=[],
        rejected_citations=[_rejected("Invented Act", "Section 1")],
        retry_count=1,
    )

    assert verification_route(state) == LEGAL_RESEARCH


def test_routes_to_supervisor_2_when_mostly_verified() -> None:
    state = _state_with(
        verified_provisions=[
            _provision("Consumer Protection Act, 2019", "Section 35"),
            _provision("Motor Vehicles Act, 1988", "Section 166"),
        ],
        rejected_citations=[_rejected("Invented Act", "Section 1")],
        retry_count=1,
    )

    assert verification_route(state) == SUPERVISOR_2


def test_routes_back_to_legal_research_on_an_even_split() -> None:
    # A tie counts as "too many rejected" — with an equal budget of
    # verified vs. rejected citations, the retry is cheap and worth
    # attempting rather than shipping a half-unusable research pass.
    state = _state_with(
        verified_provisions=[_provision("Consumer Protection Act, 2019", "Section 35")],
        rejected_citations=[_rejected("Invented Act", "Section 1")],
        retry_count=1,
    )

    assert verification_route(state) == LEGAL_RESEARCH


def test_does_not_retry_again_once_retry_budget_exhausted() -> None:
    state = _state_with(
        verified_provisions=[],
        rejected_citations=[_rejected("Invented Act", "Section 1")],
        retry_count=2,
    )

    assert verification_route(state) == SUPERVISOR_2


def test_routes_to_supervisor_2_when_nothing_was_claimed_or_rejected() -> None:
    state = _state_with(verified_provisions=[], rejected_citations=[], retry_count=1)

    assert verification_route(state) == SUPERVISOR_2


def test_routes_to_legal_research_when_verified_legal_research_missing() -> None:
    state = create_initial_state(uuid4(), uuid4())

    assert verification_route(state) == LEGAL_RESEARCH


def _evidence_state(gaps: list[EvidenceGap], pause_count: int):
    state = create_initial_state(uuid4(), uuid4())
    state["evidence_report"] = EvidenceReport(
        submitted_evidence=[], gaps=gaps, completeness_score=50.0, summary="x"
    )
    state["evidence_pause_count"] = pause_count
    return state


def test_evidence_route_pauses_on_critical_gap_under_budget() -> None:
    state = _evidence_state(
        gaps=[
            EvidenceGap(
                description="no receipt", suggested_evidence="upload receipt",
                priority=UrgencyLevel.CRITICAL,
            )
        ],
        pause_count=0,
    )

    assert evidence_analysis_route(state) == AWAITING_EVIDENCE_UPLOAD


def test_evidence_route_proceeds_when_no_critical_gap() -> None:
    state = _evidence_state(
        gaps=[
            EvidenceGap(
                description="a witness statement would help",
                suggested_evidence="witness statement",
                priority=UrgencyLevel.LOW,
            )
        ],
        pause_count=0,
    )

    assert evidence_analysis_route(state) == RISK_ASSESSMENT


def test_evidence_route_proceeds_when_pause_budget_exhausted() -> None:
    state = _evidence_state(
        gaps=[
            EvidenceGap(
                description="no receipt", suggested_evidence="upload receipt",
                priority=UrgencyLevel.CRITICAL,
            )
        ],
        pause_count=2,
    )

    assert evidence_analysis_route(state) == RISK_ASSESSMENT


def test_evidence_route_proceeds_when_no_gaps_at_all() -> None:
    state = _evidence_state(gaps=[], pause_count=0)

    assert evidence_analysis_route(state) == RISK_ASSESSMENT


def test_evidence_route_proceeds_when_report_missing() -> None:
    state = create_initial_state(uuid4(), uuid4())

    assert evidence_analysis_route(state) == RISK_ASSESSMENT
