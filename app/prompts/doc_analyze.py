"""Gemma 4 prompts for POST /api/v1/documents/analyze."""

from __future__ import annotations

from app.schemas.document_analysis import ResponseLanguage

SYSTEM_PROMPT = """You are a legal-document explainer for ordinary people in India.

Rules you MUST follow:
- Use ONLY the supplied document (text and/or image). Do not use outside knowledge.
- Quote exact passages from the document when citing clauses or risks.
- Never invent laws, section numbers, case names, or citations.
- If you are unsure, say so clearly.
- This is not legal advice. Do not tell the user what they should do legally.
- Write explanations in the requested language. If Hindi (hi), use Devanagari script.
- Keep clause quotes in the original language of the document.
- Output valid JSON only matching the schema. No markdown fences, no commentary.
"""


def build_analyze_prompt(*, language: ResponseLanguage, has_image: bool, text: str | None) -> str:
    lang_line = (
        "Respond in Hindi (Devanagari) for plain_summary, explanations, reasons, "
        "and questions_to_ask. Keep quotes in the document's original language."
        if language == "hi"
        else "Respond in simple clear English for plain_summary, explanations, "
        "reasons, and questions_to_ask. Keep quotes exactly as in the document."
    )
    source_bits: list[str] = []
    if text:
        source_bits.append(f"DOCUMENT TEXT:\n{text}")
    if has_image:
        source_bits.append(
            "An image of the document is attached. Read the visible text from the image."
        )
    source = "\n\n".join(source_bits) if source_bits else "(no text; image only)"

    return f"""Analyze this legal document for a non-lawyer in India.

{lang_line}

Produce JSON fields:
- document_type: short label (e.g. rental_agreement, notice, employment_contract)
- plain_summary: under 150 words, simple everyday language
- key_clauses: important clauses present in the document (rent, deposit, notice period,
  termination, penalties, lock-in, payment terms, etc. — only what the document contains).
  Each item needs title, quote (verbatim from the document), explanation
- risk_flags: clauses that may be unfair, harsh, or easy to miss. Each needs
  clause_title, quote (verbatim), risk_level (low|medium|high), reason
- questions_to_ask: 3 to 5 practical questions the reader should clarify

Do not invent clauses that are not in the document.

{source}
"""
