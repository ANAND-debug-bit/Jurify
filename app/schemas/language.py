"""Multilingual support (Change 9). See
docs/architecture/12-multilingual-architecture.md §12.7 for how to add a
language — a 3-step, single-PR change starting here."""

from __future__ import annotations

from enum import StrEnum


class SupportedLanguage(StrEnum):
    EN = "en"  # English
    HI = "hi"  # Hindi
    BN = "bn"  # Bengali
    TA = "ta"  # Tamil
    TE = "te"  # Telugu
    MR = "mr"  # Marathi
    GU = "gu"  # Gujarati
    PA = "pa"  # Punjabi
    KN = "kn"  # Kannada
    ML = "ml"  # Malayalam
    UR = "ur"  # Urdu
