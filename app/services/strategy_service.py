"""StrategyService — strategy plan persistence (Module 8).

Triggering the Legal Strategy Agent is Module 16's job; this service
persists/reads whatever plan it produces.
"""

from __future__ import annotations

from uuid import UUID

from app.domain.entities.strategy import Strategy
from app.domain.repositories.case_repository import CaseRepository
from app.schemas.strategy import StrategyPlan


class StrategyService:
    def __init__(self, case_repo: CaseRepository) -> None:
        self._case_repo = case_repo

    async def record_plan(self, case_id: UUID, plan: StrategyPlan) -> list[Strategy]:
        return await self._case_repo.add_strategies(case_id, plan)

    async def get_latest(self, case_id: UUID) -> list[Strategy]:
        return await self._case_repo.get_latest_strategies(case_id)
