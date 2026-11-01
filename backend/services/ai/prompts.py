"""Safety-constrained prompts for explanations and (future) chat."""

from __future__ import annotations

import json

SYSTEM_PROMPT = """You are MediExplain AI, an educational assistant that explains laboratory reports in simple language.

Rules you must follow:
1. Use only the report data supplied in the prompt. Never invent missing test values, units or reference ranges.
2. Never change or recalculate the supplied numerical values.
3. Never diagnose a disease, and never say a person "has" a condition.
4. Never prescribe or recommend medicines, doses or treatments.
5. Distinguish clearly between "outside the reference range" and "disease".
6. State uncertainty when the information is incomplete.
7. Explain medical terminology in plain language.
8. Answer in the requested language (English, Hindi, or Hinglish).
9. Encourage the user to discuss the result with a qualified healthcare professional.
10. Keep the answer under about 220 words and use the requested section headings.

You are not a doctor. Your output is educational information, not medical advice."""


def build_explanation_prompt(data: dict, language: str) -> str:
    language_name = {
        "en": "English",
        "hi": "Hindi (Devanagari script)",
        "hinglish": "Hinglish (Hindi written in Latin script, mixed with English)",
    }.get(language, "English")

    payload = json.dumps(data, ensure_ascii=False, indent=2)
    return f"""Explain ONE laboratory result from the report below.

Language: {language_name}

Report data (read-only; do not alter any number or unit):
{payload}

Use exactly these four sections, translated into the requested language:
1. What is this test?
2. What does this result show?
3. What else matters?
4. Questions you could ask your doctor

Mention the report's own reference range. If the status is UNKNOWN or NEEDS_REVIEW,
say that the result could not be reliably classified instead of guessing.
If critical_flag is true, advise the user to seek prompt medical attention and do
not offer reassurance. Do not add sections other than the four above.
"""


def build_chat_prompt(question: str, report_context: dict, retrieved_sources: list[dict], language: str) -> str:
    """Prompt for the Phase 2/3 report-grounded chatbot."""
    sources = json.dumps(retrieved_sources, ensure_ascii=False, indent=2)
    context = json.dumps(report_context, ensure_ascii=False, indent=2)
    return f"""Answer the user's question using ONLY the report context and retrieved
medical educational references below.

Language: {language}

Report context (read-only):
{context}

Retrieved references (cite the ones you use):
{sources}

User question:
{question}

If the answer is not supported by the supplied material, say that the information
is insufficient. Never diagnose, never prescribe, and never invent values.
"""
