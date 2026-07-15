"""CaseState — the LangGraph state schema every node reads from and
writes to (docs/architecture/08-pydantic-schemas.md §8.17,
docs/architecture/03-langgraph-workflow.md §3.2, v2). Composed entirely
of the agent-output contracts built in Module 6 — no node adds a new
top-level shape without also adding it here first.
"""

from __future__ import annotations

from typing import TypedDict
from uuid import UUID

from langchain_core.messages import BaseMessage

from app.domain.entities.evidence import Evidence
from app.schemas._common import CaseStatus
from app.schemas.case import CaseProfile
from app.schemas.document import GeneratedDocument
from app.schemas.emergency import EmergencyAssessment, EmergencyGuidance
from app.schemas.evidence import EvidenceReport
from app.schemas.explainability import ExplainabilityReport
from app.schemas.government_scheme import GovernmentSchemeReport
from app.schemas.judge import JudgeOpinion
from app.schemas.language import SupportedLanguage
from app.schemas.lawyer import LawyerMatch
from app.schemas.legal_research import LegalResearchResult
from app.schemas.opposition import OppositionRound
from app.schemas.risk import RiskAssessment
from app.schemas.routing import RoutingDecision
from app.schemas.strategy import StrategyPlan
from app.schemas.timeline import Timeline
from app.schemas.verification import VerifiedLegalResearchResult

DEFAULT_MAX_ROUNDS = 3


class CaseState(TypedDict):
    case_id: UUID
    user_id: UUID
    status: CaseStatus
    language: SupportedLanguage

    case_profile: CaseProfile | None
    emergency_assessment: EmergencyAssessment | None
    emergency_guidance: EmergencyGuidance | None
    timeline: Timeline | None
    legal_research: LegalResearchResult | None
    verified_legal_research: VerifiedLegalResearchResult | None
    verification_retry_count: int
    # Not an agent output like its neighbors — raw evidence is submitted
    # via its own user action (POST /case/evidence, EvidenceRepository),
    # not produced by a node. evidence_analysis_node populates this from
    # EvidenceService before running EvidenceAnalysisAgent, since agents
    # don't touch repositories directly (Module 14).
    evidence_items: list[Evidence]
    evidence_report: EvidenceReport | None
    risk_assessment: RiskAssessment | None
    strategy_plan: StrategyPlan | None
    documents: list[GeneratedDocument]
    government_scheme_report: GovernmentSchemeReport | None
    lawyer_matches: list[LawyerMatch]
    explainability_report: ExplainabilityReport | None

    stress_test_requested: bool
    opposition_rounds: list[OppositionRound]
    round_count: int
    max_rounds: int
    judge_opinion: JudgeOpinion | None

    awaiting_evidence_upload: bool
    evidence_pause_count: int

    last_routing_decision: RoutingDecision | None

    missing_fields: list[str]
    errors: list[str]
    messages: list[BaseMessage]


def create_initial_state(
    case_id: UUID,
    user_id: UUID,
    language: SupportedLanguage = SupportedLanguage.EN,
    max_rounds: int = DEFAULT_MAX_ROUNDS,
) -> CaseState:
    """A fresh, fully-populated CaseState for a just-created case — every
    optional field explicitly None/empty rather than omitted, since
    TypedDict doesn't enforce required keys at runtime and a node reading
    a missing key would KeyError instead of getting None."""
    return CaseState(
        case_id=case_id,
        user_id=user_id,
        status=CaseStatus.INTAKE_IN_PROGRESS,
        language=language,
        case_profile=None,
        emergency_assessment=None,
        emergency_guidance=None,
        timeline=None,
        legal_research=None,
        verified_legal_research=None,
        verification_retry_count=0,
        evidence_items=[],
        evidence_report=None,
        risk_assessment=None,
        strategy_plan=None,
        documents=[],
        government_scheme_report=None,
        lawyer_matches=[],
        explainability_report=None,
        stress_test_requested=False,
        opposition_rounds=[],
        round_count=0,
        max_rounds=max_rounds,
        judge_opinion=None,
        awaiting_evidence_upload=False,
        evidence_pause_count=0,
        last_routing_decision=None,
        missing_fields=[],
        errors=[],
        messages=[],
    )
