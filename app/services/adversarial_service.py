"""AdversarialService — opt-in "Stress Test My Case" entrypoint (Module 8, Change 6).

Actually running Opposition Lawyer ↔ Counter Strategy ↔ Judge is Module
21-22's job (the opt-in subgraph, docs/architecture/03-langgraph-
workflow.md §3.4); this service handles what's expressible via
CaseRepository alone: recording that the user requested a stress test,
and reading back whatever rounds already exist.
"""

from __future__ import annotations

from uuid import UUID

from app.domain.entities.opposition import OppositionRound
from app.domain.repositories.case_repository import CaseRepository


class AdversarialService:
    def __init__(self, case_repo: CaseRepository) -> None:
        self._case_repo = case_repo

    async def request_stress_test(self, case_id: UUID) -> None:
        await self._case_repo.set_stress_test_requested(case_id, True)

    async def list_rounds(self, case_id: UUID) -> list[OppositionRound]:
        return await self._case_repo.list_opposition_rounds(case_id)
