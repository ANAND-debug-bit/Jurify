"""ExplainabilityService — explainability item persistence (Module 8, Change 3).

Triggering the Explainability Agent is Module 20's job; this service
persists/reads whatever items it produces.
"""

from __future__ import annotations

from uuid import UUID

from app.domain.entities.explainability import ExplainabilityItem
from app.domain.repositories.case_repository import CaseRepository
from app.schemas.explainability import ExplainabilityReport


class ExplainabilityService:
    def __init__(self, case_repo: CaseRepository) -> None:
        self._case_repo = case_repo

    async def record_items(
        self, case_id: UUID, report: ExplainabilityReport
    ) -> list[ExplainabilityItem]:
        return await self._case_repo.add_explainability_items(case_id, report)

    async def get_latest(self, case_id: UUID) -> list[ExplainabilityItem]:
        return await self._case_repo.get_latest_explainability_items(case_id)
