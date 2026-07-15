"""Dependency injection composition root (Module 3).

Container is the single place concrete implementations get wired to the
interfaces/consumers that need them (ADR-4, docs/architecture/01-architecture-
overview.md §1.4). At this stage only cross-cutting infrastructure (settings,
logging, telemetry) exists to wire — repositories (Module 7), services
(Module 8), the LLM client, and the LangGraph orchestrator each get their own
provider method here as their own module lands. Nothing is stubbed ahead of
that; this container only exposes what already exists.

Once FastAPI routes exist, the usage pattern is `Depends(get_container)` in
a route, then `container.some_service()` — routes and services never
import a concrete repository/client class directly (ADR-4).
"""

from __future__ import annotations

from functools import lru_cache

import structlog
from opentelemetry.trace import Tracer

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.core.telemetry import configure_telemetry, get_tracer


class Container:
    """Composition root. One instance per process (see get_container()).

    Provider methods return cached/shared instances by default — the
    exception is anything whose correct lifetime is per-request or
    per-case (e.g. a Unit of Work, added in Module 4), which will be
    documented as such on the method that introduces it.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        configure_telemetry(settings)

    @property
    def settings(self) -> Settings:
        return self._settings

    def logger(self, name: str | None = None) -> structlog.stdlib.BoundLogger:
        return get_logger(name)

    def tracer(self) -> Tracer:
        return get_tracer()


@lru_cache
def get_container() -> Container:
    """Process-wide singleton container, built from the cached Settings.
    FastAPI routes (once they exist) depend on this via `Depends(get_container)`."""
    return Container(get_settings())
