"""CaseService — case lifecycle + cross-stage staleness (Module 8;
extended Module 12 with timeline persistence for the Case Reconstruction
Agent and legal research persistence for the Legal Research Agent; Module
13 with per-citation verification persistence for the Verification
Agent; Module 14 with Change 7's adaptive evidence pause/resume state;
Module 15 with a public risk-score pass-through — add_risk_score/
get_latest_risk_score existed on CaseRepository since Module 7, but
nothing exposed them to a node until now)."""

from __future__ import annotations

from uuid import UUID

from app.domain.entities.case import Case
from app.domain.entities.legal_research import LegalCitationRecord
from app.domain.entities.legal_research import LegalResearchResult as LegalResearchResultEntity
from app.domain.entities.risk import RiskScore
from app.domain.entities.timeline import CaseTimelineEvent
from app.domain.exceptions import EntityNotFoundError
from app.domain.repositories.case_repository import CaseRepository
from app.domain.repositories.evidence_repository import EvidenceRepository
from app.schemas._common import CaseStatus
from app.schemas.case import CaseProfile
from app.schemas.language import SupportedLanguage
from app.schemas.legal_research import LegalResearchResult as LegalResearchResultSchema
from app.schemas.risk import RiskAssessment
from app.schemas.timeline import Timeline
from app.schemas.verification import CitationVerification


class CaseService:
    def __init__(self, case_repo: CaseRepository, evidence_repo: EvidenceRepository) -> None:
        self._case_repo = case_repo
        self._evidence_repo = evidence_repo

    async def create_case(
        self, user_id: UUID, preferred_language: SupportedLanguage = SupportedLanguage.EN
    ) -> Case:
        return await self._case_repo.create(user_id, preferred_language)

    async def get_case(self, case_id: UUID) -> Case:
        case = await self._case_repo.get(case_id)
        if case is None:
            raise EntityNotFoundError("Case", case_id)
        return case

    async def list_cases_for_user(self, user_id: UUID) -> list[Case]:
        return await self._case_repo.list_by_user(user_id)

    async def update_status(self, case_id: UUID, status: CaseStatus) -> None:
        await self._case_repo.update_status(case_id, status)

    async def save_profile(self, case_id: UUID, profile: CaseProfile) -> None:
        await self._case_repo.update_profile(case_id, profile)

    async def save_timeline(self, case_id: UUID, timeline: Timeline) -> list[CaseTimelineEvent]:
        return await self._case_repo.add_timeline_events(case_id, timeline)

    async def get_timeline(self, case_id: UUID) -> list[CaseTimelineEvent]:
        return await self._case_repo.list_timeline_events(case_id)

    async def save_legal_research(
        self, case_id: UUID, result: LegalResearchResultSchema
    ) -> LegalResearchResultEntity:
        return await self._case_repo.add_legal_research(case_id, result)

    async def get_latest_legal_research(
        self, case_id: UUID
    ) -> LegalResearchResultEntity | None:
        return await self._case_repo.get_latest_legal_research(case_id)

    async def list_legal_citations(
        self, legal_research_result_id: UUID
    ) -> list[LegalCitationRecord]:
        return await self._case_repo.list_legal_citations(legal_research_result_id)

    async def save_citation_verifications(
        self, legal_research_result_id: UUID, verifications: list[CitationVerification]
    ) -> list[LegalCitationRecord]:
        return await self._case_repo.update_citation_verifications(
            legal_research_result_id, verifications
        )

    async def set_evidence_pause_state(
        self, case_id: UUID, *, awaiting_evidence_upload: bool, evidence_pause_count: int
    ) -> None:
        await self._case_repo.set_evidence_pause_state(
            case_id,
            awaiting_evidence_upload=awaiting_evidence_upload,
            evidence_pause_count=evidence_pause_count,
        )

    async def save_risk_score(self, case_id: UUID, risk: RiskAssessment) -> RiskScore:
        return await self._case_repo.add_risk_score(case_id, risk)

    async def get_latest_risk_score(self, case_id: UUID) -> RiskScore | None:
        return await self._case_repo.get_latest_risk_score(case_id)

    async def get_stale_stages(self, case_id: UUID) -> list[str]:
        """Which downstream stages are stale relative to the latest
        evidence submission (docs/architecture/05-api-specification.md
        §5.3, "Cascading re-runs") — computed at read time from
        timestamps, never stored, so nothing is destructively marked or
        deleted; the client decides whether to re-trigger a stale stage."""
        evidence_items = await self._evidence_repo.list_by_case(case_id)
        if not evidence_items:
            return []
        latest_evidence_at = max(item.created_at for item in evidence_items)

        stale: list[str] = []

        latest_risk = await self._case_repo.get_latest_risk_score(case_id)
        if latest_risk is not None and latest_risk.created_at < latest_evidence_at:
            stale.append("risk")

        latest_strategies = await self._case_repo.get_latest_strategies(case_id)
        if latest_strategies and latest_strategies[0].created_at < latest_evidence_at:
            stale.append("strategy")

        return stale
