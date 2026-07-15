from __future__ import annotations

from uuid import uuid4

from app.schemas.case import CaseProfile
from app.schemas.language import SupportedLanguage
from app.services.intake_service import IntakeService
from tests.unit.services.fakes import FakeCaseRepository, FakeMemoryRepository


async def test_record_user_message_and_get_history() -> None:
    case_repo = FakeCaseRepository()
    memory_repo = FakeMemoryRepository()
    service = IntakeService(case_repo, memory_repo)
    case = await case_repo.create(uuid4(), SupportedLanguage.EN)

    await service.record_user_message(case.id, "My landlord won't return my deposit", SupportedLanguage.EN)
    history = await service.get_conversation_history(case.id)

    assert len(history) == 1
    assert history[0].role == "user"
    assert history[0].language == "en"


async def test_save_profile_updates_case() -> None:
    case_repo = FakeCaseRepository()
    memory_repo = FakeMemoryRepository()
    service = IntakeService(case_repo, memory_repo)
    case = await case_repo.create(uuid4(), SupportedLanguage.EN)

    profile = CaseProfile(incident_category="tenancy_dispute", summary="deposit not returned", confidence=0.6)
    await service.save_profile(case.id, profile)

    fetched = await case_repo.get(case.id)
    assert fetched is not None
    assert fetched.case_profile is not None
    assert fetched.case_profile.incident_category == "tenancy_dispute"


async def test_record_user_message_without_language() -> None:
    case_repo = FakeCaseRepository()
    memory_repo = FakeMemoryRepository()
    service = IntakeService(case_repo, memory_repo)
    case = await case_repo.create(uuid4(), SupportedLanguage.EN)

    turn = await service.record_user_message(case.id, "hello")

    assert turn.language is None
