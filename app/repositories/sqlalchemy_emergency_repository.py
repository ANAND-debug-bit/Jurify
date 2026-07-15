"""SQLAlchemy implementation of EmergencyRepository (Module 7, Change 4)."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app.domain.entities.emergency_assessment import EmergencyAssessment
from app.schemas.emergency import EmergencyAssessment as EmergencyAssessmentSchema
from app.schemas.emergency import EmergencyGuidance


class SqlAlchemyEmergencyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_assessment(
        self,
        case_id: UUID,
        assessment: EmergencyAssessmentSchema,
        guidance: EmergencyGuidance | None = None,
    ) -> EmergencyAssessment:
        orm_assessment = models.EmergencyAssessment(
            case_id=case_id,
            is_emergency=assessment.is_emergency,
            category=assessment.category.value,
            severity=assessment.severity.value,
            rationale=assessment.rationale,
            immediate_steps=guidance.immediate_steps if guidance else None,
            evidence_preservation_checklist=(
                guidance.evidence_preservation_checklist if guidance else None
            ),
            helplines=(
                [h.model_dump() for h in guidance.helplines] if guidance else None
            ),
            recommended_authorities=(guidance.recommended_authorities if guidance else None),
        )
        self._session.add(orm_assessment)
        await self._session.flush()
        await self._session.refresh(orm_assessment)
        return EmergencyAssessment.model_validate(orm_assessment)

    async def get_latest_assessment(self, case_id: UUID) -> EmergencyAssessment | None:
        stmt = (
            select(models.EmergencyAssessment)
            .where(models.EmergencyAssessment.case_id == case_id)
            .order_by(models.EmergencyAssessment.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return EmergencyAssessment.model_validate(row) if row is not None else None
