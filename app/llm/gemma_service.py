"""Gemma 4 service interface (Me 1).

Me 2 depends on this module for document analyze/ask. The method signatures
below are the frozen contract — implement the body in a follow-up commit.
"""

from __future__ import annotations

from functools import lru_cache
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class GemmaError(Exception):
    """Raised on any Google GenAI / Gemma API failure or unparseable output."""


class GemmaService:
    """Async Gemma 4 client used by the Legal Document Intelligence API."""

    async def generate_text(
        self,
        prompt: str,
        *,
        system: str | None = None,
        thinking: bool = False,
    ) -> str:
        """Generate a plain-text completion."""
        raise NotImplementedError

    async def generate_with_image(
        self,
        prompt: str,
        image_bytes: bytes,
        mime_type: str,
        *,
        system: str | None = None,
        thinking: bool = False,
    ) -> str:
        """Generate a completion from text + an inline image."""
        raise NotImplementedError

    async def generate_structured(
        self,
        prompt: str,
        schema: type[T],
        *,
        system: str | None = None,
        image: tuple[bytes, str] | None = None,
        thinking: bool = False,
    ) -> T:
        """Generate JSON that validates as ``schema``; raise GemmaError on failure."""
        raise NotImplementedError


@lru_cache
def get_gemma_service() -> GemmaService:
    """FastAPI dependency — cached singleton GemmaService."""
    return GemmaService()
