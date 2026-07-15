from __future__ import annotations

from app.schemas.language import SupportedLanguage


def test_supports_all_eleven_indian_languages_plus_english() -> None:
    expected = {"en", "hi", "bn", "ta", "te", "mr", "gu", "pa", "kn", "ml", "ur"}
    assert {lang.value for lang in SupportedLanguage} == expected
    assert len(SupportedLanguage) == 11
