"""EvidenceService — submitted evidence persistence (Module 8), extended
Module 14 with the Evidence Analysis Agent's assessment persistence.
Change 7's adaptive pause/resume trigger lives in CaseService (the
awaiting_evidence_upload/evidence_pause_count columns belong to the
Case row, not evidence — see CaseRepository.set_evidence_pause_state).
"""

from __future__ import annotations

from uuid import UUID

from app.domain.entities.evidence import Evidence, EvidenceReport, EvidenceSubmission
from app.domain.repositories.evidence_repository import EvidenceRepository
from app.schemas.evidence import EvidenceReport as EvidenceReportSchema


class EvidenceService:
    def __init__(self, evidence_repo: EvidenceRepository) -> None:
        self._evidence_repo = evidence_repo

    async def submit_evidence(
        self, case_id: UUID, items: list[EvidenceSubmission]
    ) -> list[Evidence]:
        return await self._evidence_repo.add_items(case_id, items)

    async def list_evidence(self, case_id: UUID) -> list[Evidence]:
        return await self._evidence_repo.list_by_case(case_id)

    async def save_report(self, case_id: UUID, report: EvidenceReportSchema) -> EvidenceReport:
        return await self._evidence_repo.add_report(case_id, report)

    async def get_latest_report(self, case_id: UUID) -> EvidenceReport | None:
        return await self._evidence_repo.get_latest_report(case_id)
