"""Emergency assessment repository interface (port) (Change 4).

NEW relative to docs/architecture/06-folder-structure.md's original
domain/repositories/ list — added to match that same doc's
repositories/sqlalchemy_emergency_repository.py entry.
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.domain.entities.emergency_assessment import EmergencyAssessment
from app.schemas.emergency import EmergencyAssessment as EmergencyAssessmentSchema
from app.schemas.emergency import EmergencyGuidance


class EmergencyRepository(Protocol):
    async def add_assessment(
        self,
        case_id: UUID,
        assessment: EmergencyAssessmentSchema,
        guidance: EmergencyGuidance | None = None,
    ) -> EmergencyAssessment: ...

    async def get_latest_assessment(self, case_id: UUID) -> EmergencyAssessment | None: ...
