"""GovernmentSchemeService — scheme match persistence (Module 8, Change 5).

Triggering the Government Scheme Agent is Module 18's job; this service
persists/reads whatever matches it produces.
"""

from __future__ import annotations

from uuid import UUID

from app.domain.entities.government_scheme_match import GovernmentSchemeMatch
from app.domain.repositories.government_scheme_repository import GovernmentSchemeRepository
from app.schemas.government_scheme import GovernmentSchemeReport


class GovernmentSchemeService:
    def __init__(self, government_scheme_repo: GovernmentSchemeRepository) -> None:
        self._repo = government_scheme_repo

    async def record_matches(
        self, case_id: UUID, report: GovernmentSchemeReport
    ) -> list[GovernmentSchemeMatch]:
        return await self._repo.add_matches(case_id, report)

    async def get_latest(self, case_id: UUID) -> list[GovernmentSchemeMatch]:
        return await self._repo.get_latest_matches(case_id)
