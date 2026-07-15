import pytest
from pydantic import ValidationError

from app.core.config import (
    I18nSettings,
    Settings,
    get_settings,
)


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_settings_load_with_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in ("DATABASE_URL", "POSTGRES_USER", "REDIS_URL", "CORS_ORIGINS"):
        monkeypatch.delenv(var, raising=False)

    settings = Settings()

    assert settings.environment == "dev"
    assert settings.database.postgres_db == "nyayaos"
    assert settings.redis.redis_host == "localhost"
    assert settings.llm.llm_provider == "ollama"
    assert settings.i18n.default_language == "en"
    assert "hi" in settings.i18n.supported_languages


def test_get_settings_is_cached_singleton() -> None:
    first = get_settings()
    second = get_settings()
    assert first is second


def test_database_async_dsn_assembled_from_parts(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("POSTGRES_USER", "alice")
    monkeypatch.setenv("POSTGRES_PASSWORD", "s3cret")
    monkeypatch.setenv("POSTGRES_HOST", "db.internal")
    monkeypatch.setenv("POSTGRES_PORT", "5433")
    monkeypatch.setenv("POSTGRES_DB", "casesdb")

    settings = Settings()

    assert settings.database.async_dsn == (
        "postgresql+asyncpg://alice:s3cret@db.internal:5433/casesdb"
    )


def test_database_url_override_takes_precedence(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://explicit-dsn/whatever")

    settings = Settings()

    assert settings.database.async_dsn == "postgresql+asyncpg://explicit-dsn/whatever"


def test_cors_origins_parsed_from_csv(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORS_ORIGINS", "http://a.com, http://b.com,http://c.com")

    settings = Settings()

    assert settings.cors_origins == ["http://a.com", "http://b.com", "http://c.com"]


def test_supported_languages_parsed_from_csv(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SUPPORTED_LANGUAGES", "en,hi,ta")

    settings = I18nSettings()

    assert settings.supported_languages == ["en", "hi", "ta"]


def test_unknown_language_code_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SUPPORTED_LANGUAGES", "en,xx")

    with pytest.raises(ValidationError):
        I18nSettings()


def test_unknown_default_language_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEFAULT_LANGUAGE", "fr")

    with pytest.raises(ValidationError):
        I18nSettings()


def test_jwt_secrets_are_secret_str() -> None:
    settings = Settings()

    assert "SecretStr" in repr(settings.jwt.jwt_secret_key)
    assert settings.jwt.jwt_secret_key.get_secret_value() != repr(settings.jwt.jwt_secret_key)
