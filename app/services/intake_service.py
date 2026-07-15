"""IntakeService — case profile + conversation turn persistence (Module 8).

The "extract facts from a raw message via Gemma" step is the Case Intake
Agent's job (Module 11) — this service only covers what's expressible
via repositories: recording the user's raw message as a conversation
turn, and saving/reading the structured CaseProfile once an agent
produces one.
"""

from __future__ import annotations

from uuid import UUID

from app.domain.entities.memory import ConversationTurn
from app.domain.repositories.case_repository import CaseRepository
from app.domain.repositories.memory_repository import MemoryRepository
from app.schemas.case import CaseProfile
from app.schemas.language import SupportedLanguage


class IntakeService:
    def __init__(self, case_repo: CaseRepository, memory_repo: MemoryRepository) -> None:
        self._case_repo = case_repo
        self._memory_repo = memory_repo

    async def record_user_message(
        self, case_id: UUID, message: str, language: SupportedLanguage | None = None
    ) -> ConversationTurn:
        return await self._memory_repo.append_conversation_turn(
            case_id,
            role="user",
            content=message,
            language=language.value if language else None,
        )

    async def save_profile(self, case_id: UUID, profile: CaseProfile) -> None:
        await self._case_repo.update_profile(case_id, profile)

    async def get_conversation_history(self, case_id: UUID) -> list[ConversationTurn]:
        return await self._memory_repo.list_conversation(case_id)
