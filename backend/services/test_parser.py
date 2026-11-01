"""Rule-based line parser: turns report text into structured test results.

Design principles
-----------------
* Only values that appear in the document are extracted.
* A reference range is only taken from the document itself.
* Ambiguity is surfaced through confidence and notes instead of being hidden.
* Numeric-looking dates, page numbers and contact details are ignored.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from services import units
from services.data_normalizer import normalize_line, normalize_lookup
from services.test_catalog import TestMatch, match_test

NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")
DATE_RE = re.compile(
    r"\b\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}\b"
    r"|\b\d{4}[/.-]\d{1,2}[/.-]\d{1,2}\b"
)
TIME_RE = re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?\b")
RANGE_RE = re.compile(
    r"(?P<low>\d+(?:\.\d+)?)\s*(?:-|to)\s*(?P<high>\d+(?:\.\d+)?)",
    re.IGNORECASE,
)
UPPER_ONLY_RE = re.compile(
    r"(?:<=|<|less\s+than|upto|up\s+to)\s*(?P<high>\d+(?:\.\d+)?)",
    re.IGNORECASE,
)
LOWER_ONLY_RE = re.compile(
    r"(?:>=|>|greater\s+than)\s*(?P<low>\d+(?:\.\d+)?)",
    re.IGNORECASE,
)
FLAG_RE = re.compile(
    r"(?:^|\s)(?P<flag>HH|LL|H|L|High|Low|↑|↓)\s*$",
    re.IGNORECASE,
)
UNIT_RE = units.build_unit_pattern()

QUALITATIVE_TERMS: tuple[str, ...] = (
    "non-reactive", "non reactive", "not detected", "not-detectable",
    "reactive", "negative", "positive", "trace", "present", "absent",
    "detected", "normal", "abnormal",
)

# Lines that are clearly metadata / headings, not test rows.
NON_TEST_HINTS: tuple[str, ...] = (
    "patient", "name", "age", "sex", "gender", "date", "bill", "invoice",
    "barcode", "sample", "collected", "received", "reported", "printed",
    "doctor", "dr.", "hospital", "address", "phone", "mobile", "email",
    "uhid", "lab no", "ref by", "reference range", "bio ref", "bio. ref",
    "biological ref", "test name", "investigation", "method", "remarks",
    "interpretation", "page", "registration", "claim", "diagnosis",
)

SERIAL_PREFIX_RE = re.compile(r"^\s*\d{1,3}\s*[).:-]?\s+(?=[A-Za-z])")


@dataclass
class ParsedResult:
    test_name: str
    raw_name: str
    canonical_name: str | None
    value: float | None
    value_text: str
    unit: str
    range_low: float | None
    range_high: float | None
    range_text: str
    range_unit: str = ""
    report_flag: str = ""
    confidence: float = 0.5
    source_page: int = 1
    notes: list[str] = field(default_factory=list)
    category: str = ""


def _clean_name(text: str) -> str:
    name = text.strip(" \t:|-=_*.,")
    name = SERIAL_PREFIX_RE.sub("", name)
    name = re.sub(r"\s{2,}", " ", name).strip(" \t:|-=_*.,")
    return name[:150]


def _find_qualitative(text: str) -> str:
    lookup = normalize_lookup(text)
    for term in QUALITATIVE_TERMS:
        if re.search(rf"(?<![a-z]){re.escape(term)}(?![a-z])", lookup):
            return term
    return ""


def _extract_range(region: str) -> tuple[float | None, float | None, str, str]:
    """Return (low, high, range_text, remaining_region)."""
    match = None
    for match in RANGE_RE.finditer(region):
        pass  # choose the last range on the line (ranges sit near the end)

    if match is not None:
        low = float(match.group("low"))
        high = float(match.group("high"))
        text = match.group(0)
        remaining = region[: match.start()] + " " + region[match.end():]
        if low > high:
            low, high = high, low
        return low, high, text, remaining

    match = UPPER_ONLY_RE.search(region)
    if match is not None:
        high = float(match.group("high"))
        text = match.group(0)
        return None, high, text, region[: match.start()] + " " + region[match.end():]

    match = LOWER_ONLY_RE.search(region)
    if match is not None:
        low = float(match.group("low"))
        text = match.group(0)
        return low, None, text, region[: match.start()] + " " + region[match.end():]

    return None, None, "", region


def parse_line(line: str, page: int = 1) -> ParsedResult | None:
    # Normalise here as well so the parser is safe to call directly (tests,
    # future table handlers) rather than only through document_processor.
    text = normalize_line(line).strip()
    if len(text) < 4:
        return None
    if DATE_RE.search(text) or TIME_RE.search(text):
        return None

    match: TestMatch | None = match_test(text)
    lookup = normalize_lookup(text)

    if match is None:
        if not any(ch.isdigit() for ch in text):
            return None
        if any(hint in lookup for hint in NON_TEST_HINTS):
            return None
        # Unknown test: the name is everything before the first number.
        first_number = NUMBER_RE.search(text)
        if first_number is None:
            return None
        raw_name = _clean_name(text[: first_number.start()])
        if not raw_name or not re.search(r"[A-Za-z]", raw_name):
            return None
        region = text[first_number.start():]
        test_name = raw_name
        canonical = None
        category = ""
        base_confidence = 0.55
    else:
        if any(hint in lookup for hint in NON_TEST_HINTS) and not any(
            ch.isdigit() for ch in text
        ):
            return None
        raw_name = _clean_name(text[: match.end])
        region = text[match.end:]
        test_name = match.info.display
        canonical = match.info.canonical
        category = match.info.category
        base_confidence = 0.9

    # A trailing H/L/High/Low flag, if present.
    report_flag = ""
    flag_match = FLAG_RE.search(region)
    if flag_match is not None:
        report_flag = flag_match.group("flag").upper()
        region = region[: flag_match.start()]

    # Units can appear before or after the range. If two distinct units are
    # present, the first belongs to the value and the last to the range.
    unit_matches = list(UNIT_RE.finditer(region))
    discovered: list[str] = []
    for match_ in unit_matches:
        canonical_unit_value = units.canonical_unit(match_.group(0))
        if canonical_unit_value and canonical_unit_value not in discovered:
            discovered.append(canonical_unit_value)

    unit = discovered[0] if discovered else ""
    range_unit = discovered[-1] if len(discovered) > 1 else ""

    # Remove every unit token so only numbers and flags remain.
    for match_ in reversed(unit_matches):
        region = region[: match_.start()] + " " + region[match_.end():]

    low, high, range_text, region = _extract_range(region)
    inferred = False
    ambiguous = False

    numbers = [float(n) for n in NUMBER_RE.findall(region)]

    notes: list[str] = []
    if not numbers:
        qualitative = _find_qualitative(region) or _find_qualitative(text)
        if not qualitative:
            return None
        return ParsedResult(
            test_name=test_name,
            raw_name=raw_name or test_name,
            canonical_name=canonical,
            value=None,
            value_text=qualitative.title(),
            unit=unit,
            range_low=low,
            range_high=high,
            range_text=range_text,
            range_unit=range_unit,
            report_flag=report_flag,
            confidence=round(max(0.2, min(0.9, base_confidence - 0.1)), 2),
            source_page=page,
            notes=["Qualitative result; no numeric value to compare."],
            category=category,
        )

    value_text = NUMBER_RE.findall(region)[0]

    if range_text:
        value = numbers[0]
        if len(numbers) > 1:
            ambiguous = True
            notes.append("Multiple numeric tokens found; the first was treated as the value.")
    elif len(numbers) >= 3:
        value = numbers[0]
        low, high = numbers[1], numbers[2]
        if low > high:
            low, high = high, low
        range_text = f"{numbers[1]:g} - {numbers[2]:g}"
        inferred = True
        notes.append("Reference range inferred from three numeric columns; verify against the report.")
    else:
        value = numbers[0]
        if len(numbers) > 1:
            ambiguous = True
            notes.append("Multiple numeric tokens found; the first was treated as the value.")

    if not range_text:
        notes.append("No reference range found in this report for this test.")
    if not unit:
        notes.append("No unit detected.")
    if range_unit and unit and not units.same_unit(unit, range_unit):
        notes.append(
            f"Value unit ({unit}) and range unit ({range_unit}) differ; "
            "conversion was applied if an exact factor is known."
        )

    confidence = base_confidence
    if unit:
        confidence += 0.05
    else:
        confidence -= 0.05
    if not range_text:
        confidence -= 0.2
    if inferred:
        confidence -= 0.15
    if ambiguous:
        confidence -= 0.1
    if canonical is None:
        confidence -= 0.05
    confidence = round(max(0.2, min(0.99, confidence)), 2)

    return ParsedResult(
        test_name=test_name,
        raw_name=raw_name or test_name,
        canonical_name=canonical,
        value=value,
        value_text=value_text,
        unit=unit,
        range_low=low,
        range_high=high,
        range_text=range_text,
        range_unit=range_unit,
        report_flag=report_flag,
        confidence=confidence,
        source_page=page,
        notes=notes,
        category=category,
    )


def _is_pending_name(line: str) -> bool:
    """A test name on its own line, with the value on the next line."""
    if len(line) > 80 or any(ch.isdigit() for ch in line):
        return False
    return match_test(line) is not None


def parse_lines(lines: list[str], page: int = 1) -> list[ParsedResult]:
    results: list[ParsedResult] = []
    pending: str | None = None

    for line in lines:
        parsed = parse_line(line, page)
        if parsed is not None:
            results.append(parsed)
            pending = None
            continue

        if _is_pending_name(line):
            pending = line
            continue

        if pending and NUMBER_RE.search(line):
            merged = parse_line(f"{pending} {line}", page)
            if merged is not None:
                merged.notes.append("Name and value were on separate lines.")
                results.append(merged)
            pending = None
        elif pending and not _is_pending_name(line):
            pending = None

    return results


def deduplicate(results: list[ParsedResult]) -> list[ParsedResult]:
    """Remove duplicates caused by using both text and table extraction."""
    seen: set[tuple] = set()
    unique: list[ParsedResult] = []
    for result in results:
        key = (
            (result.canonical_name or result.test_name).lower(),
            result.value,
            result.value_text,
            units.unit_key(result.unit),
            result.range_low,
            result.range_high,
            units.unit_key(result.range_unit),
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(result)
    return unique
