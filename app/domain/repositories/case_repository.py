"""Case repository interface (port).

Case is the aggregate root (docs/architecture/01-architecture-overview.md
§1.3) — its repository also owns the child tables that have no
dedicated repository of their own (timeline events, risk scores,
strategies, documents, opposition rounds). Evidence is the one
exception, split into its own EvidenceRepository because Change 7's
adaptive pause/resume workflow needs to query/update evidence
independently of loading the rest of the case.
"""

from __future__ import annotations

from typing import Any, Protocol
from uuid import UUID

from app.domain.entities.case import Case
from app.domain.entities.document import Document
from app.domain.entities.explainability import ExplainabilityItem
from app.domain.entities.legal_research import LegalCitationRecord
from app.domain.entities.legal_research import LegalResearchResult as LegalResearchResultEntity
from app.domain.entities.opposition import OppositionRound
from app.domain.entities.risk import RiskScore
from app.domain.entities.strategy import Strategy
from app.domain.entities.timeline import CaseTimelineEvent
from app.schemas._common import CaseStatus
from app.schemas.case import CaseProfile
from app.schemas.document import GeneratedDocument
from app.schemas.explainability import ExplainabilityReport
from app.schemas.language import SupportedLanguage
from app.schemas.legal_research import LegalResearchResult as LegalResearchResultSchema
from app.schemas.risk import RiskAssessment
from app.schemas.strategy import StrategyPlan
from app.schemas.timeline import Timeline
from app.schemas.verification import CitationVerification


class CaseRepository(Protocol):
    async def get(self, case_id: UUID) -> Case | None: ...

    async def create(self, user_id: UUID, preferred_language: SupportedLanguage) -> Case: ...

    async def update_status(self, case_id: UUID, status: CaseStatus) -> None: ...

    async def update_profile(self, case_id: UUID, profile: CaseProfile) -> None: ...

    async def set_stress_test_requested(self, case_id: UUID, requested: bool = True) -> None: ...

    async def set_evidence_pause_state(
        self, case_id: UUID, *, awaiting_evidence_upload: bool, evidence_pause_count: int
    ) -> None: ...

    async def list_by_user(self, user_id: UUID) -> list[Case]: ...

    async def add_timeline_events(
        self, case_id: UUID, timeline: Timeline
    ) -> list[CaseTimelineEvent]: ...

    async def list_timeline_events(self, case_id: UUID) -> list[CaseTimelineEvent]: ...

    async def add_risk_score(self, case_id: UUID, risk: RiskAssessment) -> RiskScore: ...

    async def get_latest_risk_score(self, case_id: UUID) -> RiskScore | None: ...

    async def add_strategies(self, case_id: UUID, plan: StrategyPlan) -> list[Strategy]: ...

    async def get_latest_strategies(self, case_id: UUID) -> list[Strategy]: ...

    async def add_documents(
        self, case_id: UUID, docs: list[GeneratedDocument]
    ) -> list[Document]: ...

    async def list_documents(self, case_id: UUID) -> list[Document]: ...

    async def add_opposition_round(
        self, case_id: UUID, round_number: int, role: str, content: dict[str, Any]
    ) -> OppositionRound: ...

    async def list_opposition_rounds(self, case_id: UUID) -> list[OppositionRound]: ...

    async def add_explainability_items(
        self, case_id: UUID, report: ExplainabilityReport
    ) -> list[ExplainabilityItem]: ...

    async def get_latest_explainability_items(self, case_id: UUID) -> list[ExplainabilityItem]: ...

    async def add_legal_research(
        self, case_id: UUID, result: LegalResearchResultSchema
    ) -> LegalResearchResultEntity: ...

    async def get_latest_legal_research(
        self, case_id: UUID
    ) -> LegalResearchResultEntity | None: ...

    async def list_legal_citations(
        self, legal_research_result_id: UUID
    ) -> list[LegalCitationRecord]: ...

    async def update_citation_verifications(
        self, legal_research_result_id: UUID, verifications: list[CitationVerification]
    ) -> list[LegalCitationRecord]: ...
