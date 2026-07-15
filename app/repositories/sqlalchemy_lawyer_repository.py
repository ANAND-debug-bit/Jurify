"""SQLAlchemy implementation of LawyerRepository (Module 7).

Lawyer (= LawyerProfile, see app.domain.entities.lawyer) requires a
`fee_range_inr: tuple[float, float]` while the ORM row stores
`fee_range_min`/`fee_range_max` as two separate nullable columns —
from_attributes=True can't bridge that shape difference on its own, so
mapping is done explicitly here rather than via a blind model_validate.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app.domain.entities.lawyer import Lawyer
from app.schemas.lawyer import LawyerMatch


def _to_lawyer(orm: models.Lawyer) -> Lawyer:
    return Lawyer(
        id=orm.id,
        full_name=orm.full_name,
        specialization=orm.specialization or "",
        city=orm.city or "",
        languages=list(orm.languages) if orm.languages else [],
        fee_range_inr=(orm.fee_range_min or 0.0, orm.fee_range_max or 0.0),
        rating=orm.rating or 0.0,
        years_experience=orm.years_experience or 0,
    )


class SqlAlchemyLawyerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def search(
        self,
        *,
        city: str | None = None,
        specialization: str | None = None,
        min_rating: float | None = None,
        language: str | None = None,
    ) -> list[Lawyer]:
        stmt = select(models.Lawyer)
        if city is not None:
            stmt = stmt.where(models.Lawyer.city == city)
        if specialization is not None:
            stmt = stmt.where(models.Lawyer.specialization == specialization)
        if min_rating is not None:
            stmt = stmt.where(models.Lawyer.rating >= min_rating)
        stmt = stmt.order_by(models.Lawyer.rating.desc().nullslast())

        result = await self._session.execute(stmt)
        candidates = result.scalars().all()

        if language is not None:
            candidates = [
                lawyer for lawyer in candidates if lawyer.languages and language in lawyer.languages
            ]
        return [_to_lawyer(row) for row in candidates]

    async def get(self, lawyer_id: UUID) -> Lawyer | None:
        orm_lawyer = await self._session.get(models.Lawyer, lawyer_id)
        return _to_lawyer(orm_lawyer) if orm_lawyer is not None else None

    async def record_match(
        self, case_id: UUID, lawyer_id: UUID, match_score: float, match_reason: str
    ) -> None:
        orm_match = models.CaseLawyerMatch(
            case_id=case_id,
            lawyer_id=lawyer_id,
            match_score=match_score,
            match_reason=match_reason,
        )
        self._session.add(orm_match)
        await self._session.flush()

    async def list_matches_for_case(self, case_id: UUID) -> list[LawyerMatch]:
        stmt = (
            select(models.CaseLawyerMatch)
            .where(models.CaseLawyerMatch.case_id == case_id)
            .order_by(models.CaseLawyerMatch.match_score.desc().nullslast())
        )
        result = await self._session.execute(stmt)
        matches = result.scalars().all()

        output: list[LawyerMatch] = []
        for match in matches:
            lawyer_orm = await self._session.get(models.Lawyer, match.lawyer_id)
            if lawyer_orm is None:
                continue
            output.append(
                LawyerMatch(
                    lawyer=_to_lawyer(lawyer_orm),
                    match_score=match.match_score or 0.0,
                    match_reason=match.match_reason or "",
                )
            )
        return output
