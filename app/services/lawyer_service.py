"""LawyerService — search + match recording (Module 8).

Deciding WHEN to search/recommend (Supervisor-conditioned, Change 8) is
Module 19's job; this service covers the search and persistence
operations themselves.
"""

from __future__ import annotations

from uuid import UUID

from app.domain.entities.lawyer import Lawyer
from app.domain.repositories.lawyer_repository import LawyerRepository
from app.schemas.lawyer import LawyerMatch


class LawyerService:
    def __init__(self, lawyer_repo: LawyerRepository) -> None:
        self._lawyer_repo = lawyer_repo

    async def search(
        self,
        *,
        city: str | None = None,
        specialization: str | None = None,
        min_rating: float | None = None,
        language: str | None = None,
    ) -> list[Lawyer]:
        return await self._lawyer_repo.search(
            city=city, specialization=specialization, min_rating=min_rating, language=language
        )

    async def get(self, lawyer_id: UUID) -> Lawyer | None:
        return await self._lawyer_repo.get(lawyer_id)

    async def record_match(
        self, case_id: UUID, lawyer_id: UUID, match_score: float, match_reason: str
    ) -> None:
        await self._lawyer_repo.record_match(case_id, lawyer_id, match_score, match_reason)

    async def list_matches_for_case(self, case_id: UUID) -> list[LawyerMatch]:
        return await self._lawyer_repo.list_matches_for_case(case_id)
