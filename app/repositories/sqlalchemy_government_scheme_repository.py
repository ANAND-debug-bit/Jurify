"""SQLAlchemy implementation of GovernmentSchemeRepository (Module 7, Change 5).

The ORM column is `scheme_name` (a plain string) while the domain
entity's field is `scheme` (a GovernmentScheme enum) — from_attributes
can't bridge a name mismatch, so mapping is explicit here rather than a
blind model_validate.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app.domain.entities.government_scheme_match import GovernmentSchemeMatch
from app.schemas.government_scheme import GovernmentScheme, GovernmentSchemeReport


def _to_government_scheme_match(orm: models.GovernmentSchemeMatch) -> GovernmentSchemeMatch:
    return GovernmentSchemeMatch(
        id=orm.id,
        case_id=orm.case_id,
        scheme=GovernmentScheme(orm.scheme_name),
        eligible=orm.eligible,
        confidence=orm.confidence,
        documents_required=list(orm.documents_required) if orm.documents_required else [],
        how_to_apply=orm.how_to_apply,
        relevant_authority=orm.relevant_authority,
        created_at=orm.created_at,
    )


class SqlAlchemyGovernmentSchemeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_matches(
        self, case_id: UUID, report: GovernmentSchemeReport
    ) -> list[GovernmentSchemeMatch]:
        orm_matches = [
            models.GovernmentSchemeMatch(
                case_id=case_id,
                scheme_name=match.scheme.value,
                eligible=match.eligible,
                confidence=match.confidence,
                documents_required=match.documents_required,
                how_to_apply=match.how_to_apply,
                relevant_authority=match.relevant_authority,
            )
            for match in report.matches
        ]
        self._session.add_all(orm_matches)
        await self._session.flush()
        for orm_match in orm_matches:
            await self._session.refresh(orm_match)
        return [_to_government_scheme_match(m) for m in orm_matches]

    async def get_latest_matches(self, case_id: UUID) -> list[GovernmentSchemeMatch]:
        # See SqlAlchemyCaseRepository.get_latest_strategies for why this
        # is computed from an already-typed result set rather than a
        # separate func.max(...) comparison query.
        stmt = (
            select(models.GovernmentSchemeMatch)
            .where(models.GovernmentSchemeMatch.case_id == case_id)
            .order_by(models.GovernmentSchemeMatch.created_at.desc())
        )
        result = await self._session.execute(stmt)
        all_matches = result.scalars().all()
        if not all_matches:
            return []
        latest_created_at = all_matches[0].created_at
        latest_batch = [m for m in all_matches if m.created_at == latest_created_at]
        return [_to_government_scheme_match(row) for row in latest_batch]
