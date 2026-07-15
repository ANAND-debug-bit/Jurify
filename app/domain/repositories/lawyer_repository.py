"""Lawyer repository interface (port). Backs GET /lawyers search and the
Lawyer Recommendation Agent's match-recording (docs/architecture/05-api-
specification.md §5.2)."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.domain.entities.lawyer import Lawyer
from app.schemas.lawyer import LawyerMatch


class LawyerRepository(Protocol):
    async def search(
        self,
        *,
        city: str | None = None,
        specialization: str | None = None,
        min_rating: float | None = None,
        language: str | None = None,
    ) -> list[Lawyer]: ...

    async def get(self, lawyer_id: UUID) -> Lawyer | None: ...

    async def record_match(
        self, case_id: UUID, lawyer_id: UUID, match_score: float, match_reason: str
    ) -> None: ...

    async def list_matches_for_case(self, case_id: UUID) -> list[LawyerMatch]: ...
