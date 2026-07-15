"""SQLAlchemy implementation of EvidenceRepository (Module 7, extended
Module 14 with EvidenceReport persistence)."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app.domain.entities.evidence import Evidence, EvidenceReport, EvidenceSubmission
from app.schemas.evidence import EvidenceReport as EvidenceReportSchema


class SqlAlchemyEvidenceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_items(
        self, case_id: UUID, items: list[EvidenceSubmission]
    ) -> list[Evidence]:
        orm_items = [
            models.Evidence(
                case_id=case_id,
                evidence_type=item.evidence_type,
                description=item.description,
                file_url=item.file_url,
            )
            for item in items
        ]
        self._session.add_all(orm_items)
        await self._session.flush()
        for orm_item in orm_items:
            await self._session.refresh(orm_item)
        return [Evidence.model_validate(item) for item in orm_items]

    async def list_by_case(self, case_id: UUID) -> list[Evidence]:
        stmt = (
            select(models.Evidence)
            .where(models.Evidence.case_id == case_id)
            .order_by(models.Evidence.created_at)
        )
        result = await self._session.execute(stmt)
        return [Evidence.model_validate(row) for row in result.scalars().all()]

    async def add_report(self, case_id: UUID, report: EvidenceReportSchema) -> EvidenceReport:
        submitted_evidence = [item.model_dump(mode="json") for item in report.submitted_evidence]
        gaps = [gap.model_dump(mode="json") for gap in report.gaps]
        orm_report = models.EvidenceReport(
            case_id=case_id,
            submitted_evidence=submitted_evidence,
            gaps=gaps,
            completeness_score=report.completeness_score,
            summary=report.summary,
        )
        self._session.add(orm_report)
        await self._session.flush()
        await self._session.refresh(orm_report)
        return EvidenceReport.model_validate(orm_report)

    async def get_latest_report(self, case_id: UUID) -> EvidenceReport | None:
        stmt = (
            select(models.EvidenceReport)
            .where(models.EvidenceReport.case_id == case_id)
            .order_by(models.EvidenceReport.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return EvidenceReport.model_validate(row) if row is not None else None
