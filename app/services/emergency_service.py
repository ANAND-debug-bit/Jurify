"""EmergencyService — emergency assessment + guidance persistence
(Module 11, Change 4).

Not in docs/architecture/06-folder-structure.md's original services/
list — added here because graph/nodes/emergency_detection_node.py and
emergency_agent_node.py need a service to persist through, matching the
same gap-closing pattern used for EmergencyRepository (Module 7).

Deciding WHEN to run the Emergency Detection/Emergency agents is the
graph's job (docs/architecture/03-langgraph-workflow.md §3.7); this
service only persists/reads whatever they produce.
"""

from __future__ import annotations

from uuid import UUID

from app.domain.entities.emergency_assessment import EmergencyAssessment
from app.domain.repositories.emergency_repository import EmergencyRepository
from app.schemas.emergency import EmergencyAssessment as EmergencyAssessmentSchema
from app.schemas.emergency import EmergencyGuidance


class EmergencyService:
    def __init__(self, emergency_repo: EmergencyRepository) -> None:
        self._emergency_repo = emergency_repo

    async def record_assessment(
        self,
        case_id: UUID,
        assessment: EmergencyAssessmentSchema,
        guidance: EmergencyGuidance | None = None,
    ) -> EmergencyAssessment:
        return await self._emergency_repo.add_assessment(case_id, assessment, guidance)

    async def get_latest_assessment(self, case_id: UUID) -> EmergencyAssessment | None:
        return await self._emergency_repo.get_latest_assessment(case_id)
