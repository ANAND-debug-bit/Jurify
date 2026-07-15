"""RiskService — risk assessment persistence (Module 8).

Triggering the Risk Assessment Agent is Module 15's job; this service
persists/reads whatever assessment it produces.
"""

from __future__ import annotations

from uuid import UUID

from app.domain.entities.risk import RiskScore
from app.domain.repositories.case_repository import CaseRepository
from app.schemas.risk import RiskAssessment


class RiskService:
    def __init__(self, case_repo: CaseRepository) -> None:
        self._case_repo = case_repo

    async def record_assessment(self, case_id: UUID, assessment: RiskAssessment) -> RiskScore:
        return await self._case_repo.add_risk_score(case_id, assessment)

    async def get_latest(self, case_id: UUID) -> RiskScore | None:
        return await self._case_repo.get_latest_risk_score(case_id)
