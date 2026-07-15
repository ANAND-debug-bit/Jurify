"""Government scheme match repository interface (port) (Change 5).

NEW relative to docs/architecture/06-folder-structure.md's original
domain/repositories/ list — added to match that same doc's
repositories/sqlalchemy_government_scheme_repository.py entry.
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.domain.entities.government_scheme_match import GovernmentSchemeMatch
from app.schemas.government_scheme import GovernmentSchemeReport


class GovernmentSchemeRepository(Protocol):
    async def add_matches(
        self, case_id: UUID, report: GovernmentSchemeReport
    ) -> list[GovernmentSchemeMatch]: ...

    async def get_latest_matches(self, case_id: UUID) -> list[GovernmentSchemeMatch]: ...
