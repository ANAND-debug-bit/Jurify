"""Evidence repository interface (port).

Split out from CaseRepository because Change 7's adaptive evidence
pause/resume workflow needs to query/update evidence independently of
loading the rest of the case (docs/architecture/03-langgraph-workflow.md
§3.6).
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.domain.entities.evidence import Evidence, EvidenceReport, EvidenceSubmission
from app.schemas.evidence import EvidenceReport as EvidenceReportSchema


class EvidenceRepository(Protocol):
    async def add_items(
        self, case_id: UUID, items: list[EvidenceSubmission]
    ) -> list[Evidence]: ...

    async def list_by_case(self, case_id: UUID) -> list[Evidence]: ...

    async def add_report(self, case_id: UUID, report: EvidenceReportSchema) -> EvidenceReport: ...

    async def get_latest_report(self, case_id: UUID) -> EvidenceReport | None: ...
