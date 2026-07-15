"""Shared test fixtures/helpers across the whole suite."""

from __future__ import annotations

import urllib.request
from functools import lru_cache

from app.core.config import get_settings


@lru_cache
def ollama_is_reachable() -> bool:
    """Best-effort check for a local Ollama server — used to gate the
    small number of live-LLM tests that call a real Gemma model instead
    of a fake, so the suite still passes in environments without Ollama
    running (e.g. CI). Cached for the process lifetime; these are dev-
    machine smoke tests, not something that flips mid-run."""
    settings = get_settings()
    if settings.llm.llm_provider != "ollama":
        return False
    try:
        with urllib.request.urlopen(f"{settings.llm.ollama_base_url}/api/version", timeout=1):
            return True
    except OSError:
        return False
