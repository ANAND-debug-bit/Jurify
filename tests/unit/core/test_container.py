import pytest

from app.core import telemetry
from app.core.config import Settings
from app.core.container import Container, get_container


@pytest.fixture(autouse=True)
def _reset_container_cache():
    get_container.cache_clear()
    yield
    get_container.cache_clear()


def test_get_container_is_cached_singleton() -> None:
    first = get_container()
    second = get_container()

    assert first is second


def test_container_exposes_the_settings_it_was_built_with() -> None:
    settings = Settings(environment="dev")

    container = Container(settings)

    assert container.settings is settings


def test_container_logger_returns_bound_logger_with_expected_api() -> None:
    container = Container(Settings())

    logger = container.logger("test.container")

    assert hasattr(logger, "info")
    assert hasattr(logger, "bind")
    assert hasattr(logger, "exception")


def test_container_logger_defaults_to_unnamed_logger() -> None:
    container = Container(Settings())

    logger = container.logger()

    assert hasattr(logger, "info")


def test_container_tracer_returns_usable_tracer() -> None:
    container = Container(Settings())

    tracer = container.tracer()

    assert hasattr(tracer, "start_as_current_span")


def test_container_construction_configures_telemetry() -> None:
    telemetry._configured = False

    Container(Settings(environment="dev"))

    assert telemetry._configured is True


def test_get_container_uses_process_settings_singleton() -> None:
    from app.core.config import get_settings

    container = get_container()

    assert container.settings is get_settings()
