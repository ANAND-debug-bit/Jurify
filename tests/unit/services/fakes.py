"""In-memory fake repositories for unit-testing services against
repository *fakes* rather than a real database
(docs/architecture/14-testing-and-implementation-plan.md §14.1) — pure
Python, no SQLAlchemy, no event loop I/O. Each fake implements the exact
same Protocol its SQLAlchemy counterpart does (app.domain.repositories),
so services are exercised through the real interface.
"""

from __future__ import annotations

import itertools
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from app.domain.entities.case import Case
from app.domain.entities.document import Document
from app.domain.entities.emergency_assessment import EmergencyAssessment
from app.domain.entities.evidence import Evidence
from app.domain.entities.evidence import EvidenceReport as EvidenceReportEntity
from app.domain.entities.evidence import EvidenceSubmission
from app.domain.entities.explainability import ExplainabilityItem
from app.domain.entities.government_scheme_match import GovernmentSchemeMatch
from app.domain.entities.lawyer import Lawyer
from app.domain.entities.legal_research import LegalCitationRecord
from app.domain.entities.legal_research import LegalResearchResult as LegalResearchResultEntity
from app.domain.entities.memory import ConversationTurn, LongTermMemoryRecord
from app.domain.entities.opposition import OppositionRound
from app.domain.entities.risk import RiskScore
from app.domain.entities.strategy import Strategy
from app.domain.entities.timeline import CaseTimelineEvent
from app.domain.exceptions import EntityNotFoundError
from app.schemas._common import CaseStatus
from app.schemas.case import CaseProfile
from app.schemas.document import GeneratedDocument
from app.schemas.emergency import EmergencyAssessment as EmergencyAssessmentSchema
from app.schemas.emergency import EmergencyGuidance
from app.schemas.evidence import EvidenceReport as EvidenceReportSchema
from app.schemas.explainability import ExplainabilityReport
from app.schemas.government_scheme import GovernmentSchemeReport
from app.schemas.language import SupportedLanguage
from app.schemas.lawyer import LawyerMatch
from app.schemas.legal_research import LegalResearchResult as LegalResearchResultSchema
from app.schemas.risk import RiskAssessment
from app.schemas.strategy import StrategyPlan
from app.schemas.timeline import Timeline
from app.schemas.verification import CitationVerification


# Strictly monotonic, even across calls faster than the system clock's
# actual resolution — two rows created back-to-back in the same test must
# never tie, or "latest" comparisons (used throughout these fakes and by
# CaseService.get_stale_stages) become order-dependent and flaky.
_tick = itertools.count()
_EPOCH = datetime(2020, 1, 1, tzinfo=UTC)


def _now() -> datetime:
    return _EPOCH + timedelta(microseconds=next(_tick))


class FakeCaseRepository:
    def __init__(self) -> None:
        self.cases: dict[UUID, Case] = {}
        self.timeline_events: dict[UUID, list[CaseTimelineEvent]] = {}
        self.risk_scores: dict[UUID, list[RiskScore]] = {}
        self.strategies: dict[UUID, list[Strategy]] = {}
        self.documents: dict[UUID, list[Document]] = {}
        self.opposition_rounds: dict[UUID, list[OppositionRound]] = {}
        self.explainability_items: dict[UUID, list[ExplainabilityItem]] = {}
        self.legal_research: dict[UUID, list[LegalResearchResultEntity]] = {}
        self.legal_citations: dict[UUID, list[LegalCitationRecord]] = {}

    async def get(self, case_id: UUID) -> Case | None:
        return self.cases.get(case_id)

    async def create(self, user_id: UUID, preferred_language: SupportedLanguage) -> Case:
        now = _now()
        case = Case(
            id=uuid4(),
            user_id=user_id,
            status=CaseStatus.INTAKE_IN_PROGRESS,
            preferred_language=preferred_language,
            created_at=now,
            updated_at=now,
        )
        self.cases[case.id] = case
        return case

    async def update_status(self, case_id: UUID, status: CaseStatus) -> None:
        case = self.cases.get(case_id)
        if case is None:
            raise EntityNotFoundError("Case", case_id)
        case.status = status

    async def update_profile(self, case_id: UUID, profile: CaseProfile) -> None:
        case = self.cases.get(case_id)
        if case is None:
            raise EntityNotFoundError("Case", case_id)
        case.case_profile = profile
        case.incident_category = profile.incident_category

    async def set_stress_test_requested(self, case_id: UUID, requested: bool = True) -> None:
        case = self.cases.get(case_id)
        if case is None:
            raise EntityNotFoundError("Case", case_id)
        case.stress_test_requested = requested

    async def set_evidence_pause_state(
        self, case_id: UUID, *, awaiting_evidence_upload: bool, evidence_pause_count: int
    ) -> None:
        case = self.cases.get(case_id)
        if case is None:
            raise EntityNotFoundError("Case", case_id)
        case.awaiting_evidence_upload = awaiting_evidence_upload
        case.evidence_pause_count = evidence_pause_count

    async def list_by_user(self, user_id: UUID) -> list[Case]:
        return [c for c in self.cases.values() if c.user_id == user_id]

    async def add_timeline_events(
        self, case_id: UUID, timeline: Timeline
    ) -> list[CaseTimelineEvent]:
        events = [
            CaseTimelineEvent(
                id=uuid4(),
                case_id=case_id,
                occurred_at=event.occurred_at,
                description=event.description,
                is_inconsistent=event.is_inconsistent,
                inconsistency_note=event.inconsistency_note,
                sequence_order=event.sequence_order,
            )
            for event in timeline.events
        ]
        self.timeline_events.setdefault(case_id, []).extend(events)
        return events

    async def list_timeline_events(self, case_id: UUID) -> list[CaseTimelineEvent]:
        return sorted(
            self.timeline_events.get(case_id, []), key=lambda e: e.sequence_order
        )

    async def add_risk_score(self, case_id: UUID, risk: RiskAssessment) -> RiskScore:
        score = RiskScore(
            id=uuid4(),
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
            created_at=_now(),
        )
        self.risk_scores.setdefault(case_id, []).append(score)
        return score

    async def get_latest_risk_score(self, case_id: UUID) -> RiskScore | None:
        scores = self.risk_scores.get(case_id, [])
        return max(scores, key=lambda s: s.created_at) if scores else None

    async def add_strategies(self, case_id: UUID, plan: StrategyPlan) -> list[Strategy]:
        now = _now()
        strategies = [
            Strategy(
                id=uuid4(),
                case_id=case_id,
                forum=option.forum.value,
                estimated_cost=option.estimated_cost_inr,
                estimated_time=option.estimated_time,
                difficulty=option.difficulty,
                success_probability=option.success_probability,
                is_recommended=(index == plan.recommended_option_index),
                created_at=now,
            )
            for index, option in enumerate(plan.options)
        ]
        self.strategies.setdefault(case_id, []).extend(strategies)
        return strategies

    async def get_latest_strategies(self, case_id: UUID) -> list[Strategy]:
        all_strategies = self.strategies.get(case_id, [])
        if not all_strategies:
            return []
        latest_created_at = max(s.created_at for s in all_strategies)
        return [s for s in all_strategies if s.created_at == latest_created_at]

    async def add_documents(
        self, case_id: UUID, docs: list[GeneratedDocument]
    ) -> list[Document]:
        now = _now()
        documents = [
            Document(
                id=uuid4(),
                case_id=case_id,
                document_type=doc.document_type.value,
                title=doc.title,
                content=doc.content,
                recipient=doc.recipient,
                filing_authority=doc.filing_authority,
                status="draft",
                created_at=now,
            )
            for doc in docs
        ]
        self.documents.setdefault(case_id, []).extend(documents)
        return documents

    async def list_documents(self, case_id: UUID) -> list[Document]:
        return list(self.documents.get(case_id, []))

    async def add_opposition_round(
        self, case_id: UUID, round_number: int, role: str, content: dict[str, Any]
    ) -> OppositionRound:
        round_ = OppositionRound(
            id=uuid4(),
            case_id=case_id,
            round_number=round_number,
            role=role,
            content=content,
            created_at=_now(),
        )
        self.opposition_rounds.setdefault(case_id, []).append(round_)
        return round_

    async def list_opposition_rounds(self, case_id: UUID) -> list[OppositionRound]:
        return sorted(
            self.opposition_rounds.get(case_id, []), key=lambda r: r.round_number
        )

    async def add_explainability_items(
        self, case_id: UUID, report: ExplainabilityReport
    ) -> list[ExplainabilityItem]:
        now = _now()
        items = [
            ExplainabilityItem(
                id=uuid4(),
                case_id=case_id,
                conclusion=item.conclusion,
                reasoning=item.reasoning,
                supporting_evidence_refs=item.supporting_evidence_refs,
                supporting_legal_refs=item.supporting_legal_refs,
                confidence_score=item.confidence_score,
                missing_information=item.missing_information,
                created_at=now,
            )
            for item in report.items
        ]
        self.explainability_items.setdefault(case_id, []).extend(items)
        return items

    async def get_latest_explainability_items(self, case_id: UUID) -> list[ExplainabilityItem]:
        all_items = self.explainability_items.get(case_id, [])
        if not all_items:
            return []
        latest_created_at = max(i.created_at for i in all_items)
        return [i for i in all_items if i.created_at == latest_created_at]

    async def add_legal_research(
        self, case_id: UUID, result: LegalResearchResultSchema
    ) -> LegalResearchResultEntity:
        entity = LegalResearchResultEntity(
            id=uuid4(),
            case_id=case_id,
            jurisdiction=result.jurisdiction,
            applicable_laws=result.applicable_laws,
            plain_explanation=result.overall_summary,
            created_at=_now(),
        )
        self.legal_research.setdefault(case_id, []).append(entity)
        self.legal_citations[entity.id] = [
            LegalCitationRecord(
                id=uuid4(),
                legal_research_result_id=entity.id,
                act_name=citation.act_name,
                section=citation.section,
                source_url=citation.source_url,
                excerpt=citation.excerpt,
                is_verified=False,
                verification_status="unverified",
                verification_notes=None,
                verified_at=None,
            )
            for law in result.applicable_laws
            for citation in law.citations
        ]
        return entity

    async def get_latest_legal_research(
        self, case_id: UUID
    ) -> LegalResearchResultEntity | None:
        records = self.legal_research.get(case_id, [])
        return max(records, key=lambda r: r.created_at) if records else None

    async def list_legal_citations(
        self, legal_research_result_id: UUID
    ) -> list[LegalCitationRecord]:
        return list(self.legal_citations.get(legal_research_result_id, []))

    async def update_citation_verifications(
        self, legal_research_result_id: UUID, verifications: list[CitationVerification]
    ) -> list[LegalCitationRecord]:
        # Mirrors SqlAlchemyCaseRepository.update_citation_verifications'
        # match-by-(act_name, section) semantics exactly, so tests against
        # this fake exercise the same matching behavior as the real repo.
        rows = self.legal_citations.get(legal_research_result_id, [])
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
            match.verified_at = _now()
            updated_ids.add(match.id)
        return list(rows)


class FakeEvidenceRepository:
    def __init__(self) -> None:
        self.items: dict[UUID, list[Evidence]] = {}
        self.reports: dict[UUID, list[EvidenceReportEntity]] = {}

    async def add_items(
        self, case_id: UUID, items: list[EvidenceSubmission]
    ) -> list[Evidence]:
        now = _now()
        added = [
            Evidence(
                id=uuid4(),
                case_id=case_id,
                evidence_type=item.evidence_type,
                description=item.description,
                file_url=item.file_url,
                created_at=now,
            )
            for item in items
        ]
        self.items.setdefault(case_id, []).extend(added)
        return added

    async def list_by_case(self, case_id: UUID) -> list[Evidence]:
        return list(self.items.get(case_id, []))

    async def add_report(
        self, case_id: UUID, report: EvidenceReportSchema
    ) -> EvidenceReportEntity:
        entity = EvidenceReportEntity(
            id=uuid4(),
            case_id=case_id,
            submitted_evidence=report.submitted_evidence,
            gaps=report.gaps,
            completeness_score=report.completeness_score,
            summary=report.summary,
            created_at=_now(),
        )
        self.reports.setdefault(case_id, []).append(entity)
        return entity

    async def get_latest_report(self, case_id: UUID) -> EvidenceReportEntity | None:
        records = self.reports.get(case_id, [])
        return max(records, key=lambda r: r.created_at) if records else None


class FakeLawyerRepository:
    def __init__(self) -> None:
        self.lawyers: dict[UUID, Lawyer] = {}
        self.matches: dict[UUID, list[LawyerMatch]] = {}

    async def search(
        self,
        *,
        city: str | None = None,
        specialization: str | None = None,
        min_rating: float | None = None,
        language: str | None = None,
    ) -> list[Lawyer]:
        results = list(self.lawyers.values())
        if city is not None:
            results = [lw for lw in results if lw.city == city]
        if specialization is not None:
            results = [lw for lw in results if lw.specialization == specialization]
        if min_rating is not None:
            results = [lw for lw in results if lw.rating >= min_rating]
        if language is not None:
            results = [lw for lw in results if language in lw.languages]
        return results

    async def get(self, lawyer_id: UUID) -> Lawyer | None:
        return self.lawyers.get(lawyer_id)

    async def record_match(
        self, case_id: UUID, lawyer_id: UUID, match_score: float, match_reason: str
    ) -> None:
        lawyer = self.lawyers[lawyer_id]
        self.matches.setdefault(case_id, []).append(
            LawyerMatch(lawyer=lawyer, match_score=match_score, match_reason=match_reason)
        )

    async def list_matches_for_case(self, case_id: UUID) -> list[LawyerMatch]:
        return list(self.matches.get(case_id, []))


class FakeMemoryRepository:
    def __init__(self) -> None:
        self.conversation: dict[UUID, list[ConversationTurn]] = {}
        self.long_term: dict[UUID, list[LongTermMemoryRecord]] = {}

    async def append_conversation_turn(
        self, case_id: UUID, role: str, content: str, language: str | None
    ) -> ConversationTurn:
        turn = ConversationTurn(
            id=uuid4(), case_id=case_id, role=role, content=content, language=language, created_at=_now()
        )
        self.conversation.setdefault(case_id, []).append(turn)
        return turn

    async def list_conversation(self, case_id: UUID) -> list[ConversationTurn]:
        return list(self.conversation.get(case_id, []))

    async def save_long_term_memory(
        self,
        user_id: UUID,
        memory_type: str,
        content: dict[str, object],
        embedding: list[float] | None = None,
    ) -> LongTermMemoryRecord:
        record = LongTermMemoryRecord(
            id=uuid4(),
            user_id=user_id,
            memory_type=memory_type,
            content=content,
            embedding=embedding,
            created_at=_now(),
        )
        self.long_term.setdefault(user_id, []).append(record)
        return record

    async def list_long_term_memory(self, user_id: UUID) -> list[LongTermMemoryRecord]:
        return list(self.long_term.get(user_id, []))


class FakeGovernmentSchemeRepository:
    def __init__(self) -> None:
        self.matches: dict[UUID, list[GovernmentSchemeMatch]] = {}

    async def add_matches(
        self, case_id: UUID, report: GovernmentSchemeReport
    ) -> list[GovernmentSchemeMatch]:
        now = _now()
        added = [
            GovernmentSchemeMatch(
                id=uuid4(),
                case_id=case_id,
                scheme=match.scheme,
                eligible=match.eligible,
                confidence=match.confidence,
                documents_required=match.documents_required,
                how_to_apply=match.how_to_apply,
                relevant_authority=match.relevant_authority,
                created_at=now,
            )
            for match in report.matches
        ]
        self.matches.setdefault(case_id, []).extend(added)
        return added

    async def get_latest_matches(self, case_id: UUID) -> list[GovernmentSchemeMatch]:
        all_matches = self.matches.get(case_id, [])
        if not all_matches:
            return []
        latest_created_at = max(m.created_at for m in all_matches)
        return [m for m in all_matches if m.created_at == latest_created_at]


class FakeEmergencyRepository:
    def __init__(self) -> None:
        self.assessments: dict[UUID, list[EmergencyAssessment]] = {}

    async def add_assessment(
        self,
        case_id: UUID,
        assessment: EmergencyAssessmentSchema,
        guidance: EmergencyGuidance | None = None,
    ) -> EmergencyAssessment:
        record = EmergencyAssessment(
            id=uuid4(),
            case_id=case_id,
            is_emergency=assessment.is_emergency,
            category=assessment.category,
            severity=assessment.severity,
            rationale=assessment.rationale,
            immediate_steps=guidance.immediate_steps if guidance else None,
            evidence_preservation_checklist=(
                guidance.evidence_preservation_checklist if guidance else None
            ),
            helplines=[h.model_dump() for h in guidance.helplines] if guidance else None,
            recommended_authorities=guidance.recommended_authorities if guidance else None,
            created_at=_now(),
        )
        self.assessments.setdefault(case_id, []).append(record)
        return record

    async def get_latest_assessment(self, case_id: UUID) -> EmergencyAssessment | None:
        records = self.assessments.get(case_id, [])
        return max(records, key=lambda r: r.created_at) if records else None
