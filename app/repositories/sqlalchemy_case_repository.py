"""SQLAlchemy implementation of CaseRepository (Module 7, extended
Modules 8 and 12).

Owns the Case aggregate root plus every child table without its own
repository (timeline events, risk scores, strategies, documents,
opposition rounds, explainability items, legal research results) — see
app.domain.repositories.case_repository for the rationale.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app.domain.entities.case import Case
from app.domain.entities.document import Document
from app.domain.entities.explainability import ExplainabilityItem
from app.domain.entities.legal_research import LegalCitationRecord
from app.domain.entities.legal_research import LegalResearchResult as LegalResearchResultEntity
from app.domain.entities.opposition import OppositionRound
from app.domain.entities.risk import RiskScore
from app.domain.entities.strategy import Strategy
from app.domain.entities.timeline import CaseTimelineEvent
from app.domain.exceptions import EntityNotFoundError
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


class SqlAlchemyCaseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, case_id: UUID) -> Case | None:
        orm_case = await self._session.get(models.Case, case_id)
        return Case.model_validate(orm_case) if orm_case is not None else None

    async def create(self, user_id: UUID, preferred_language: SupportedLanguage) -> Case:
        orm_case = models.Case(
            user_id=user_id,
            status=CaseStatus.INTAKE_IN_PROGRESS.value,
            preferred_language=preferred_language.value,
        )
        self._session.add(orm_case)
        await self._session.flush()
        await self._session.refresh(orm_case)
        return Case.model_validate(orm_case)

    async def update_status(self, case_id: UUID, status: CaseStatus) -> None:
        orm_case = await self._session.get(models.Case, case_id)
        if orm_case is None:
            raise EntityNotFoundError("Case", case_id)
        orm_case.status = status.value
        await self._session.flush()

    async def update_profile(self, case_id: UUID, profile: CaseProfile) -> None:
        orm_case = await self._session.get(models.Case, case_id)
        if orm_case is None:
            raise EntityNotFoundError("Case", case_id)
        orm_case.case_profile = profile.model_dump(mode="json")
        orm_case.incident_category = profile.incident_category
        await self._session.flush()

    async def set_stress_test_requested(self, case_id: UUID, requested: bool = True) -> None:
        orm_case = await self._session.get(models.Case, case_id)
        if orm_case is None:
            raise EntityNotFoundError("Case", case_id)
        orm_case.stress_test_requested = requested
        await self._session.flush()

    async def set_evidence_pause_state(
        self, case_id: UUID, *, awaiting_evidence_upload: bool, evidence_pause_count: int
    ) -> None:
        orm_case = await self._session.get(models.Case, case_id)
        if orm_case is None:
            raise EntityNotFoundError("Case", case_id)
        orm_case.awaiting_evidence_upload = awaiting_evidence_upload
        orm_case.evidence_pause_count = evidence_pause_count
        await self._session.flush()

    async def list_by_user(self, user_id: UUID) -> list[Case]:
        stmt = (
            select(models.Case)
            .where(models.Case.user_id == user_id)
            .order_by(models.Case.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return [Case.model_validate(row) for row in result.scalars().all()]

    async def add_timeline_events(
        self, case_id: UUID, timeline: Timeline
    ) -> list[CaseTimelineEvent]:
        orm_events = [
            models.CaseTimelineEvent(
                case_id=case_id,
                occurred_at=event.occurred_at,
                description=event.description,
                is_inconsistent=event.is_inconsistent,
                inconsistency_note=event.inconsistency_note,
                sequence_order=event.sequence_order,
            )
            for event in timeline.events
        ]
        self._session.add_all(orm_events)
        await self._session.flush()
        for orm_event in orm_events:
            await self._session.refresh(orm_event)
        return [CaseTimelineEvent.model_validate(e) for e in orm_events]

    async def list_timeline_events(self, case_id: UUID) -> list[CaseTimelineEvent]:
        stmt = (
            select(models.CaseTimelineEvent)
            .where(models.CaseTimelineEvent.case_id == case_id)
            .order_by(models.CaseTimelineEvent.sequence_order)
        )
        result = await self._session.execute(stmt)
        return [CaseTimelineEvent.model_validate(row) for row in result.scalars().all()]

    async def add_risk_score(self, case_id: UUID, risk: RiskAssessment) -> RiskScore:
        orm_risk = models.RiskScore(
            case_id=case_id,
            financial_risk=risk.financial_risk,
            criminal_risk=risk.criminal_risk,
            urgency_level=risk.urgency.value,
            needs_police=risk.needs_police,
            needs_lawyer=risk.needs_lawyer,
            needs_medical=risk.needs_medical,
            settlement_probability=risk.settlement_probability,
            case_strength=risk.case_strength,
            rationale=risk.rationale,
        )
        self._session.add(orm_risk)
        await self._session.flush()
        await self._session.refresh(orm_risk)
        return RiskScore.model_validate(orm_risk)

    async def get_latest_risk_score(self, case_id: UUID) -> RiskScore | None:
        stmt = (
            select(models.RiskScore)
            .where(models.RiskScore.case_id == case_id)
            .order_by(models.RiskScore.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return RiskScore.model_validate(row) if row is not None else None

    async def add_strategies(self, case_id: UUID, plan: StrategyPlan) -> list[Strategy]:
        orm_strategies = [
            models.Strategy(
                case_id=case_id,
                forum=option.forum.value,
                estimated_cost=option.estimated_cost_inr,
                estimated_time=option.estimated_time,
                difficulty=option.difficulty,
                success_probability=option.success_probability,
                is_recommended=(index == plan.recommended_option_index),
            )
            for index, option in enumerate(plan.options)
        ]
        self._session.add_all(orm_strategies)
        await self._session.flush()
        for orm_strategy in orm_strategies:
            await self._session.refresh(orm_strategy)
        return [Strategy.model_validate(s) for s in orm_strategies]

    async def get_latest_strategies(self, case_id: UUID) -> list[Strategy]:
        # Strategies are versioned by created_at as a batch (§4.2) — all
        # options from one add_strategies() call share the same
        # created_at within a transaction (func.now() is transaction-
        # stable on Postgres), so grouping on the max created_at recovers
        # "the latest planning pass" rather than just the latest row.
        #
        # Deliberately not a separate func.max(...) query compared via
        # `== max_created_at`: some dialects (SQLite included) don't
        # apply the column's normal type-processing to aggregate results,
        # so a datetime returned by MAX() can fail to compare equal to
        # the same value read through a plain SELECT. Comparing within
        # one already-typed result set sidesteps that entirely.
        stmt = (
            select(models.Strategy)
            .where(models.Strategy.case_id == case_id)
            .order_by(models.Strategy.created_at.desc())
        )
        result = await self._session.execute(stmt)
        all_strategies = result.scalars().all()
        if not all_strategies:
            return []
        latest_created_at = all_strategies[0].created_at
        latest_batch = [s for s in all_strategies if s.created_at == latest_created_at]
        return [Strategy.model_validate(row) for row in latest_batch]

    async def add_documents(
        self, case_id: UUID, docs: list[GeneratedDocument]
    ) -> list[Document]:
        orm_docs = [
            models.Document(
                case_id=case_id,
                document_type=doc.document_type.value,
                title=doc.title,
                content=doc.content,
                recipient=doc.recipient,
                filing_authority=doc.filing_authority,
                status="draft",
            )
            for doc in docs
        ]
        self._session.add_all(orm_docs)
        await self._session.flush()
        for orm_doc in orm_docs:
            await self._session.refresh(orm_doc)
        return [Document.model_validate(d) for d in orm_docs]

    async def list_documents(self, case_id: UUID) -> list[Document]:
        stmt = (
            select(models.Document)
            .where(models.Document.case_id == case_id)
            .order_by(models.Document.created_at)
        )
        result = await self._session.execute(stmt)
        return [Document.model_validate(row) for row in result.scalars().all()]

    async def add_opposition_round(
        self, case_id: UUID, round_number: int, role: str, content: dict[str, Any]
    ) -> OppositionRound:
        orm_round = models.OppositionRound(
            case_id=case_id, round_number=round_number, role=role, content=content
        )
        self._session.add(orm_round)
        await self._session.flush()
        await self._session.refresh(orm_round)
        return OppositionRound.model_validate(orm_round)

    async def list_opposition_rounds(self, case_id: UUID) -> list[OppositionRound]:
        stmt = (
            select(models.OppositionRound)
            .where(models.OppositionRound.case_id == case_id)
            .order_by(models.OppositionRound.round_number)
        )
        result = await self._session.execute(stmt)
        return [OppositionRound.model_validate(row) for row in result.scalars().all()]

    async def add_explainability_items(
        self, case_id: UUID, report: ExplainabilityReport
    ) -> list[ExplainabilityItem]:
        orm_items = [
            models.ExplainabilityReport(
                case_id=case_id,
                conclusion=item.conclusion,
                reasoning=item.reasoning,
                supporting_evidence_refs=item.supporting_evidence_refs,
                supporting_legal_refs=item.supporting_legal_refs,
                confidence_score=item.confidence_score,
                missing_information=item.missing_information,
            )
            for item in report.items
        ]
        self._session.add_all(orm_items)
        await self._session.flush()
        for orm_item in orm_items:
            await self._session.refresh(orm_item)
        return [ExplainabilityItem.model_validate(item) for item in orm_items]

    async def get_latest_explainability_items(self, case_id: UUID) -> list[ExplainabilityItem]:
        # See get_latest_strategies for why "latest batch" is computed
        # from an already-typed result set rather than a separate
        # func.max(...) comparison query.
        stmt = (
            select(models.ExplainabilityReport)
            .where(models.ExplainabilityReport.case_id == case_id)
            .order_by(models.ExplainabilityReport.created_at.desc())
        )
        result = await self._session.execute(stmt)
        all_items = result.scalars().all()
        if not all_items:
            return []
        latest_created_at = all_items[0].created_at
        latest_batch = [item for item in all_items if item.created_at == latest_created_at]
        return [ExplainabilityItem.model_validate(row) for row in latest_batch]

    async def add_legal_research(
        self, case_id: UUID, result: LegalResearchResultSchema
    ) -> LegalResearchResultEntity:
        orm_result = models.LegalResearchResult(
            case_id=case_id,
            jurisdiction=result.jurisdiction,
            applicable_laws=[law.model_dump(mode="json") for law in result.applicable_laws],
            plain_explanation=result.overall_summary,
        )
        self._session.add(orm_result)
        await self._session.flush()

        # Every citation inside every provision is also exploded into its
        # own legal_citations row (unverified by default) — the
        # Verification Agent (Module 13) updates verification status per
        # row independently of the JSONB blob above.
        orm_citations = [
            models.LegalCitation(
                legal_research_result_id=orm_result.id,
                act_name=citation.act_name,
                section=citation.section,
                source_url=citation.source_url,
                excerpt=citation.excerpt,
            )
            for law in result.applicable_laws
            for citation in law.citations
        ]
        self._session.add_all(orm_citations)
        await self._session.flush()
        await self._session.refresh(orm_result)
        return LegalResearchResultEntity.model_validate(orm_result)

    async def get_latest_legal_research(
        self, case_id: UUID
    ) -> LegalResearchResultEntity | None:
        stmt = (
            select(models.LegalResearchResult)
            .where(models.LegalResearchResult.case_id == case_id)
            .order_by(models.LegalResearchResult.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return LegalResearchResultEntity.model_validate(row) if row is not None else None

    async def list_legal_citations(
        self, legal_research_result_id: UUID
    ) -> list[LegalCitationRecord]:
        stmt = select(models.LegalCitation).where(
            models.LegalCitation.legal_research_result_id == legal_research_result_id
        )
        result = await self._session.execute(stmt)
        return [LegalCitationRecord.model_validate(row) for row in result.scalars().all()]

    async def update_citation_verifications(
        self, legal_research_result_id: UUID, verifications: list[CitationVerification]
    ) -> list[LegalCitationRecord]:
        # Matched by (act_name, section) within this research pass rather
        # than by row id — the Verification Agent's output schema
        # (CitationVerification) only carries the citation content it was
        # given, never a DB id, so it can't reference rows directly. A
        # research pass with duplicate act_name+section citations across
        # provisions is a known, accepted limitation: only the first
        # matching row is updated per verification.
        stmt = select(models.LegalCitation).where(
            models.LegalCitation.legal_research_result_id == legal_research_result_id
        )
        result = await self._session.execute(stmt)
        rows = list(result.scalars().all())
        updated_ids: set[UUID] = set()

        for verification in verifications:
            match = next(
                (
                    row
                    for row in rows
                    if row.id not in updated_ids
                    and row.act_name == verification.citation.act_name
                    and row.section == verification.citation.section
                ),
                None,
            )
            if match is None:
                continue
            match.is_verified = verification.status.value == "verified"
            match.verification_status = verification.status.value
            match.verification_notes = verification.verification_notes
            match.verified_at = datetime.now(UTC)
            updated_ids.add(match.id)

        await self._session.flush()
        for row in rows:
            await self._session.refresh(row)
        return [LegalCitationRecord.model_validate(row) for row in rows]
