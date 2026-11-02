"""Report-grounded chat with deterministic safety and offline fallback.

The chatbot is deliberately narrow: it can only talk about the results that
were extracted from one report. Questions asking for a diagnosis, medicine or
treatment are refused before the model is called. When no LLM is available the
engine still answers common questions with deterministic templates, so the
feature is usable (and testable) offline.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Optional, Sequence

from services.ai import prompts
from services.ai.llm_provider import LLMProvider
from services.explanation_service import (
    CONTEXT_TEXT,
    CRITICAL_TEXT,
    LABELS,
    LANGUAGES,
    STATUS_TEXT,
    ResultContext,
    basic_info,
)
from services.medical_analyzer import (
    ABNORMAL_STATUSES,
    STATUS_NORMAL,
    STATUS_NOT_AVAILABLE,
    STATUS_UNKNOWN,
)

logger = logging.getLogger(__name__)

MAX_HISTORY_TURNS = 10

# Words that identify a test even when the report prints a slightly different
# name. Matching uses word boundaries, so short aliases such as "hb" stay safe.
TEST_ALIASES: dict[str, tuple[str, ...]] = {
    "hemoglobin": ("hemoglobin", "haemoglobin", "hb"),
    "wbc": ("wbc", "white blood", "leukocyte", "twbc", "tlc"),
    "platelets": ("platelet", "platelets", "plt"),
    "rbc": ("rbc", "red blood", "erythrocyte"),
    "hematocrit": ("hematocrit", "pcv", "hct"),
    "mcv": ("mcv", "mean corpuscular volume"),
    "mch": ("mch",),
    "mchc": ("mchc",),
    "neutrophils": ("neutrophil", "neutrophils"),
    "lymphocytes": ("lymphocyte", "lymphocytes"),
    "monocytes": ("monocyte", "monocytes"),
    "eosinophils": ("eosinophil", "eosinophils"),
    "basophils": ("basophil", "basophils"),
    "glucose": ("glucose", "sugar", "fbs", "ppbs", "blood sugar"),
    "fasting_glucose": ("fasting glucose", "fasting sugar", "fbs"),
    "random_glucose": ("random glucose", "random sugar", "rbs"),
    "hba1c": ("hba1c", "a1c", "glycated hemoglobin"),
    "total_cholesterol": ("total cholesterol", "cholesterol"),
    "hdl": ("hdl", "good cholesterol"),
    "ldl": ("ldl", "bad cholesterol"),
    "triglycerides": ("triglyceride", "triglycerides", "tg"),
    "creatinine": ("creatinine",),
    "urea": ("urea", "bun", "blood urea"),
    "tsh": ("tsh", "thyroid"),
    "t3": ("t3", "triiodothyronine"),
    "t4": ("t4", "thyroxine"),
    "vitamin_d": ("vitamin d", "vit d", "25-oh"),
    "vitamin_b12": ("vitamin b12", "b12"),
    "sgot": ("sgot", "ast"),
    "sgpt": ("sgpt", "alt"),
    "bilirubin_total": ("bilirubin",),
    "crp": ("crp", "c-reactive"),
    "potassium": ("potassium", "k+"),
    "sodium": ("sodium", "na+"),
    "calcium": ("calcium",),
    "uric_acid": ("uric acid", "urate"),
    "esr": ("esr", "sedimentation"),
}

_SAFETY_PATTERNS = (
    re.compile(
        r"\b(medicine|medicines|medication|medications|tablet|tablets|dose|dosage|"
        r"prescri\w*|antibiotic\w*|treatment|treat|therapy|cure|remedy|dawa|dawai|"
        r"davai|ilaaj|ilaj)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(do i have|do we have|diagnos\w*|am i (diabetic|anemic|anaemic)|"
        r"kya mujhe|mujhe kya bimari|is it (cancer|diabetes|anemia|anaemia|thyroid)|"
        r"confirm\w*)\b",
        re.IGNORECASE,
    ),
)

_SUMMARY_RE = re.compile(
    r"\b(abnormal|out of range|outside|high|low|normal|summary|overall|report|"
    r"results?|concern|worry|problem|everything|theek|thik|kaisi|sab)\b",
    re.IGNORECASE,
)
_CRITICAL_RE = re.compile(
    r"\b(critical|urgent|emergency|danger|serious|turant|jaldi)\b", re.IGNORECASE
)
_ADVICE_RE = re.compile(
    r"\b(what should i do|what to do|next step|should i worry|kya karu|kya karna|"
    r"kya karein|doctor|consult)\b",
    re.IGNORECASE,
)


@dataclass
class ChatAnswer:
    text: str
    model: str
    source: str
    cited_result_ids: list[int]


def _lang(language: str) -> str:
    return language if language in LANGUAGES else "en"


def _value_repr(ctx: ResultContext) -> str:
    if ctx.value is not None:
        text = ctx.value_text or f"{ctx.value:g}"
        return f"{text} {ctx.unit}".strip()
    return ctx.value_text or STATUS_TEXT["en"][STATUS_NOT_AVAILABLE]


def _range_repr(ctx: ResultContext, language: str) -> str:
    if not ctx.range_text:
        return LABELS[language]["range_missing"]
    unit = ctx.range_unit or ctx.unit
    unit_text = f" {unit}" if unit else ""
    return f"{ctx.range_text}{unit_text}"


def _status_label(ctx: ResultContext, language: str) -> str:
    return LABELS[language].get(ctx.status, ctx.status)


def _is_unsafe(question: str) -> bool:
    return any(pattern.search(question) for pattern in _SAFETY_PATTERNS)


def _alias_pattern(alias: str) -> re.Pattern[str]:
    return re.compile(rf"\b{re.escape(alias)}\b", re.IGNORECASE)


def _result_aliases(ctx: ResultContext) -> tuple[str, ...]:
    aliases: list[str] = []
    for value in (ctx.canonical_name or "", ctx.test_name):
        if value:
            aliases.append(value)
    aliases.extend(TEST_ALIASES.get(ctx.canonical_name or "", ()))
    # Longest aliases first so "fasting glucose" wins over "glucose".
    return tuple(sorted({alias.lower() for alias in aliases if alias}, key=len, reverse=True))


def match_results(question: str, results: Sequence[ResultContext]) -> list[ResultContext]:
    """Return report results whose name or alias is mentioned in the question."""
    matched: list[ResultContext] = []
    for result in results:
        if any(_alias_pattern(alias).search(question) for alias in _result_aliases(result)):
            matched.append(result)
    return matched


def _citations(
    question: str,
    results: Sequence[ResultContext],
    matched: Sequence[ResultContext],
) -> list[int]:
    if matched:
        return [result.result_id for result in matched]
    if _CRITICAL_RE.search(question):
        critical = [result for result in results if result.critical_flag]
        if critical:
            return [result.result_id for result in critical]
    if _SUMMARY_RE.search(question):
        abnormal = [result for result in results if result.status in ABNORMAL_STATUSES]
        if abnormal:
            return [result.result_id for result in abnormal]
    return []


def _format_result_line(ctx: ResultContext, language: str) -> str:
    return (
        f"- {ctx.test_name}: {_value_repr(ctx)} "
        f"(range {_range_repr(ctx, language)}) — {_status_label(ctx, language)}"
    )


def _critical_sentence(results: Sequence[ResultContext], language: str) -> str:
    critical = [result.test_name for result in results if result.critical_flag]
    if not critical:
        return ""
    names = ", ".join(critical)
    if language == "hi":
        return (
            f"**आपातकालीन ध्यान:** इस रिपोर्ट में {names} के लिए critical-value नियम चिह्नित हुआ है। "
            "कृपया तुरंत चिकित्सकीय सहायता लें; इस ऐप पर आपातकालीन निर्णय के लिए निर्भर न रहें।"
        )
    if language == "hinglish":
        return (
            f"**Urgent:** is report mein {names} ke liye critical-value rule flag hua hai. "
            "Kripya turant medical help lein; urgent decision ke liye is app par depend na karein."
        )
    return (
        f"**Urgent:** critical-value rules flagged {names} in this report. "
        "Please seek prompt medical attention; do not rely on this app for an emergency decision."
    )


def _refusal(results: Sequence[ResultContext], language: str) -> ChatAnswer:
    critical = _critical_sentence(results, language)
    critical_ids = [result.result_id for result in results if result.critical_flag]
    if language == "hi":
        text = (
            "मैं किसी बीमारी का निदान नहीं कर सकता और न ही दवा, खुराक या इलाज बता सकता हूँ। "
            "इसके लिए योग्य चिकित्सक आवश्यक है जो आपकी जाँच कर सके और इतिहास देख सके। "
            "मैं इस रिपोर्ट के मानों और संदर्भ सीमाओं का अर्थ समझा सकता हूँ।"
        )
    elif language == "hinglish":
        text = (
            "Main kisi bimari ka diagnosis nahi kar sakta aur na hi medicine, dose ya treatment "
            "bata sakta hoon. Iske liye qualified clinician zaroori hai jo aapko examine kar sake "
            "aur history dekh sake. Main is report ki values aur reference ranges ka matlab "
            "samjha sakta hoon."
        )
    else:
        text = (
            "I can't diagnose a condition or recommend medicines, doses or treatment. That needs a "
            "qualified clinician who can examine you, review your history and arrange any further "
            "tests. I can explain what the values and reference ranges in this report mean."
        )
    if critical:
        text = f"{critical}\n\n{text}"
    return ChatAnswer(
        text=text,
        model="template",
        source="template",
        cited_result_ids=critical_ids,
    )


def _specific_answer(
    matched: Sequence[ResultContext], language: str
) -> ChatAnswer:
    blocks: list[str] = []
    for ctx in matched[:3]:
        value = _value_repr(ctx)
        range_text = _range_repr(ctx, language)
        status = _status_label(ctx, language)
        status_text = STATUS_TEXT[language].get(ctx.status, STATUS_TEXT[language][STATUS_UNKNOWN])
        range_prefix = {
            "en": "Reference range",
            "hi": "संदर्भ सीमा",
            "hinglish": "Reference range",
        }[language]
        block = (
            f"**{ctx.test_name}**\n"
            f"{value} — {status}. {range_prefix}: {range_text}.\n\n"
            f"{status_text}\n\n"
            f"{basic_info(ctx.canonical_name, ctx.test_name, language)}\n\n"
            f"{CONTEXT_TEXT[language]}"
        )
        if ctx.critical_flag:
            block = f"{block}\n\n{CRITICAL_TEXT[language]}"
        blocks.append(block)

    if len(matched) > 3:
        extra = len(matched) - 3
        if language == "hi":
            blocks.append(f"इस रिपोर्ट में {extra} और संबंधित परिणाम हैं; कृपया तालिका देखें।")
        elif language == "hinglish":
            blocks.append(f"Is report mein {extra} aur related results hain; kripya table dekhein.")
        else:
            blocks.append(f"There are {extra} more related results in the table above.")

    return ChatAnswer(
        text="\n\n".join(blocks),
        model="template",
        source="template",
        cited_result_ids=[ctx.result_id for ctx in matched],
    )


def _summary_answer(
    results: Sequence[ResultContext], language: str
) -> ChatAnswer:
    abnormal = [result for result in results if result.status in ABNORMAL_STATUSES]
    normal_count = sum(1 for result in results if result.status == STATUS_NORMAL)
    unclassified = len(results) - len(abnormal) - normal_count
    critical = _critical_sentence(results, language)

    if language == "hi":
        header = "**रिपोर्ट सारांश**"
        if abnormal:
            counts = (
                f"इस रिपोर्ट में {len(results)} परिणाम हैं: {len(abnormal)} रिपोर्ट में दी गई संदर्भ सीमा से बाहर "
                f"और {normal_count} सीमा के भीतर हैं"
            )
            if unclassified:
                counts += f"; {unclassified} वर्गीकृत नहीं हैं"
            lines = [
                f"{counts}।",
                "",
                "सीमा से बाहर:",
                *[_format_result_line(result, language) for result in abnormal],
                "",
                "सीमा से बाहर होना अपने आप किसी बीमारी का निदान नहीं है। कृपया इन परिणामों पर योग्य चिकित्सक से चर्चा करें।",
            ]
        else:
            lines = [
                f"इस रिपोर्ट में {len(results)} परिणाम हैं और सभी वर्गीकृत परिणाम रिपोर्ट में दी गई "
                "संदर्भ सीमा के भीतर हैं।",
                "",
                "सीमा के भीतर होना हर स्वास्थ्य स्थिति को बाहर नहीं करता; लक्षण हों तो चिकित्सक से मिलें।",
            ]
    elif language == "hinglish":
        header = "**Report summary**"
        if abnormal:
            counts = (
                f"Is report mein {len(results)} results hain: {len(abnormal)} report ki reference range se "
                f"bahar aur {normal_count} range ke andar"
            )
            if unclassified:
                counts += f"; {unclassified} classify nahi hue"
            lines = [
                f"{counts}.",
                "",
                "Range se bahar:",
                *[_format_result_line(result, language) for result in abnormal],
                "",
                "Range se bahar hona apne aap kisi bimari ka diagnosis nahi hai. Kripya in results par "
                "qualified doctor se baat karein.",
            ]
        else:
            lines = [
                f"Is report mein {len(results)} results hain aur saare classified results report ki "
                "reference range ke andar hain.",
                "",
                "Range ke andar hona har health condition ko rule out nahi karta; symptoms ho to doctor se milein.",
            ]
    else:
        header = "**Report summary**"
        if abnormal:
            counts = (
                f"This report has {len(results)} results: {len(abnormal)} outside the reference ranges "
                f"printed on the report and {normal_count} within them"
            )
            if unclassified:
                counts += f"; {unclassified} could not be classified"
            lines = [
                f"{counts}.",
                "",
                "Out of range:",
                *[_format_result_line(result, language) for result in abnormal],
                "",
                "An out-of-range value is not by itself a diagnosis. Please discuss these results with "
                "a qualified healthcare professional.",
            ]
        else:
            lines = [
                f"This report has {len(results)} results and every classified result is inside the "
                "reference range printed on the report.",
                "",
                "Being inside the range does not rule out every health condition; speak to a clinician "
                "if you have symptoms.",
            ]

    text = "\n".join([header, ""] + lines)
    if critical:
        text = f"{critical}\n\n{text}"

    return ChatAnswer(
        text=text,
        model="template",
        source="template",
        cited_result_ids=[result.result_id for result in abnormal],
    )


def _critical_answer(
    results: Sequence[ResultContext], language: str
) -> ChatAnswer:
    critical = [result for result in results if result.critical_flag]
    sentence = _critical_sentence(results, language)

    if critical:
        lines = [
            sentence,
            "",
            "Flagged results:",
            *[_format_result_line(result, language) for result in critical],
            "",
            (
                "These thresholds are demonstration placeholders and are not clinically validated. "
                "Please contact a healthcare professional promptly and do not wait for an AI answer."
                if language == "en"
                else (
                    "ये सीमाएँ केवल प्रदर्शन के लिए हैं और नैदानिक रूप से सत्यापित नहीं हैं। "
                    "कृपया शीघ्र चिकित्सकीय सहायता लें।"
                    if language == "hi"
                    else "Yeh thresholds sirf demonstration ke liye hain aur clinically validated nahi hain. "
                    "Kripya turant medical help lein."
                )
            ),
        ]
    else:
        lines = [
            (
                "No result in this report triggered the app's critical-value rules. That does not rule "
                "out an urgent problem: if you have severe symptoms, seek medical care immediately."
                if language == "en"
                else (
                    "इस रिपोर्ट में किसी परिणाम ने critical-value नियम नहीं भड़काया। इसका मतलब यह नहीं कि "
                    "कोई आपातकालीन समस्या नहीं है; गंभीर लक्षण हों तो तुरंत चिकित्सकीय सहायता लें।"
                    if language == "hi"
                    else "Is report mein kisi result ne critical-value rule trigger nahi kiya. Iska matlab "
                    "yeh nahi ki urgent problem nahi hai; severe symptoms ho to turant medical help lein."
                )
            )
        ]

    return ChatAnswer(
        text="\n".join(lines),
        model="template",
        source="template",
        cited_result_ids=[result.result_id for result in critical],
    )


def _advice_answer(
    results: Sequence[ResultContext], language: str
) -> ChatAnswer:
    abnormal = [result for result in results if result.status in ABNORMAL_STATUSES]
    critical = _critical_sentence(results, language)
    if language == "hi":
        lines = [
            "मैं यह नहीं बता सकता कि आपको क्या करना चाहिए या क्या आपको चिंता करनी चाहिए — यह आपके लक्षणों, "
            "इतिहास और जाँच के संदर्भ में चिकित्सक का निर्णय है।",
            "",
        ]
        if abnormal:
            lines.append("इस रिपोर्ट में सीमा से बाहर:")
            lines.extend(_format_result_line(result, language) for result in abnormal)
            lines.append("")
        lines.append("कृपया यह रिपोर्ट अपने डॉक्टर के साथ साझा करें और अगले कदम पर चर्चा करें।")
    elif language == "hinglish":
        lines = [
            "Main yeh nahi bata sakta ki aapko kya karna chahiye ya worry karni chahiye — yeh aapke "
            "symptoms, history aur test ke context mein clinician ka decision hai.",
            "",
        ]
        if abnormal:
            lines.append("Is report mein range se bahar:")
            lines.extend(_format_result_line(result, language) for result in abnormal)
            lines.append("")
        lines.append("Kripya yeh report apne doctor ke saath share karein aur next step par baat karein.")
    else:
        lines = [
            "I can't tell you what to do or whether to worry — that depends on your symptoms, history "
            "and examination, which need a clinician.",
            "",
        ]
        if abnormal:
            lines.append("Results outside the range printed on this report:")
            lines.extend(_format_result_line(result, language) for result in abnormal)
            lines.append("")
        lines.append("Please share this report with your doctor and discuss the next step together.")

    text = "\n".join(lines)
    if critical:
        text = f"{critical}\n\n{text}"
    return ChatAnswer(
        text=text,
        model="template",
        source="template",
        cited_result_ids=[result.result_id for result in abnormal],
    )


def _fallback_answer(
    question: str, results: Sequence[ResultContext], language: str
) -> ChatAnswer:
    names = ", ".join(result.test_name for result in results[:12])
    if len(results) > 12:
        names += ", …"
    if language == "hi":
        text = (
            "मैं केवल इस रिपोर्ट से निकाले गए परिणामों के आधार पर उत्तर दे सकता हूँ। "
            f"इस रिपोर्ट में ये जाँचें हैं: {names}।\n\n"
            "कृपया किसी जाँच का नाम लेकर पूछें, जैसे “हीमोग्लोबिन का क्या मतलब है?” या "
            "“कौन से परिणाम सीमा से बाहर हैं?”।"
        )
    elif language == "hinglish":
        text = (
            "Main sirf is report se extracted results ke basis par answer de sakta hoon. "
            f"Is report mein yeh tests hain: {names}.\n\n"
            "Kripya kisi test ka naam le kar poochhein, jaise “Hemoglobin ka kya matlab hai?” ya "
            "“Kaun se results range se bahar hain?”."
        )
    else:
        text = (
            "I can only answer using the results extracted from this report. "
            f"The tests in this report are: {names}.\n\n"
            "Try asking about one of them, for example “What does hemoglobin mean?” or "
            "“Which results are out of range?”."
        )
    return ChatAnswer(text=text, model="template", source="template", cited_result_ids=[])


def _result_payload(ctx: ResultContext) -> dict:
    return {
        "result_id": ctx.result_id,
        "test_name": ctx.test_name,
        "value": ctx.value,
        "value_text": ctx.value_text,
        "unit": ctx.unit,
        "reference_range": {
            "text": ctx.range_text,
            "low": ctx.range_low,
            "high": ctx.range_high,
            "unit": ctx.range_unit or ctx.unit,
            "reported": bool(ctx.range_text),
        },
        "status": ctx.status,
        "critical_flag": ctx.critical_flag,
    }


class ChatEngine:
    def __init__(self, provider: Optional[LLMProvider] = None) -> None:
        self.provider = provider
        self._provider_failed = False

    def answer(
        self,
        question: str,
        results: Sequence[ResultContext],
        language: str,
        history: Sequence[tuple[str, str]] = (),
    ) -> ChatAnswer:
        language = _lang(language)

        # Safety rules apply whether or not a model is available.
        if _is_unsafe(question):
            return _refusal(results, language)

        matched = match_results(question, results)
        cited = _citations(question, results, matched)

        if self.provider is not None and not self._provider_failed:
            try:
                transcript = "\n".join(
                    f"{'User' if role == 'user' else 'Assistant'}: {content[:800]}"
                    for role, content in history[-MAX_HISTORY_TURNS:]
                )
                text = self.provider.generate(
                    prompts.CHAT_SYSTEM_PROMPT,
                    prompts.build_chat_prompt(
                        question=question,
                        report_context={
                            "results": [_result_payload(result) for result in results],
                        },
                        retrieved_sources=[],
                        language=language,
                        history=transcript,
                    ),
                )
                if len(text.strip()) >= 20:
                    return ChatAnswer(
                        text=text.strip(),
                        model=self.provider.model or "unknown",
                        source=self.provider.name,
                        cited_result_ids=cited,
                    )
                logger.warning("LLM returned an unusably short chat answer; using template.")
                self._provider_failed = True
            except Exception as exc:  # noqa: BLE001 - any provider failure degrades safely
                logger.warning(
                    "AI provider unavailable (%s); falling back to template chat.",
                    type(exc).__name__,
                )
                self._provider_failed = True

        if matched:
            return _specific_answer(matched, language)
        if _CRITICAL_RE.search(question):
            return _critical_answer(results, language)
        if _ADVICE_RE.search(question):
            return _advice_answer(results, language)
        if _SUMMARY_RE.search(question):
            return _summary_answer(results, language)
        return _fallback_answer(question, results, language)
