"""Async Unit of Work (Module 4).

Wraps a single AsyncSession's transactional boundary: commit on clean
exit, rollback on exception, always close. Repositories (Module 7) will
be constructed from the UnitOfWork's session so multiple repository
writes within one `async with UnitOfWork() as uow:` block share a single
transaction and commit atomically together — this is what lets, e.g., the
Risk Assessment node write both a `risk_scores` row and its `agent_logs`
row as one all-or-nothing unit (docs/architecture/01-architecture-
overview.md §1.4).
"""

from __future__ import annotations

from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.database.session import get_sessionmaker


class UnitOfWork:
    def __init__(
        self, session_factory: async_sessionmaker[AsyncSession] | None = None
    ) -> None:
        self._session_factory = session_factory or get_sessionmaker()
        self._session: AsyncSession | None = None

    @property
    def session(self) -> AsyncSession:
        if self._session is None:
            raise RuntimeError("UnitOfWork used outside of an 'async with' block")
        return self._session

    async def __aenter__(self) -> Self:
        self._session = self._session_factory()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        session = self.session
        try:
            if exc_type is None:
                await session.commit()
            else:
                await session.rollback()
        finally:
            await session.close()
            self._session = None

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()
