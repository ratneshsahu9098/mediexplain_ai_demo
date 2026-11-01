"""Deterministic analysis engine: compare values against the report's ranges.

The LLM is never involved here. This module decides NORMAL/LOW/HIGH/UNKNOWN,
so classification remains reproducible and testable.
"""

from __future__ import annotations

from dataclasses import dataclass

from services import critical_values, units
from services.test_parser import ParsedResult

STATUS_NORMAL = "NORMAL"
STATUS_LOW = "LOW"
STATUS_HIGH = "HIGH"
STATUS_UNKNOWN = "UNKNOWN"
STATUS_NOT_AVAILABLE = "NOT_AVAILABLE"
STATUS_NEEDS_REVIEW = "NEEDS_REVIEW"
STATUS_QUALITATIVE = "QUALITATIVE"

ABNORMAL_STATUSES = frozenset({STATUS_LOW, STATUS_HIGH})


@dataclass
class Analysis:
    status: str
    critical_flag: bool
    unit_converted: bool
    notes: str


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and value == value  # NaN check


def analyze_result(result: ParsedResult) -> Analysis:
    notes = list(result.notes)

    if result.value is None:
        if result.value_text:
            return Analysis(STATUS_QUALITATIVE, False, False, " ".join(notes))
        return Analysis(STATUS_NOT_AVAILABLE, False, False, " ".join(notes))

    low = result.range_low
    high = result.range_high
    if low is None and high is None:
        notes.append("No reference interval supplied by the report; not classified.")
        return Analysis(STATUS_UNKNOWN, False, False, " ".join(dict.fromkeys(notes)))

    if (low is not None and not _is_number(low)) or (
        high is not None and not _is_number(high)
    ):
        notes.append("Reference interval could not be interpreted; needs review.")
        return Analysis(STATUS_NEEDS_REVIEW, False, False, " ".join(dict.fromkeys(notes)))

    compare_value = float(result.value)
    compare_unit = result.unit
    range_unit = result.range_unit or result.unit
    converted = False

    if result.unit and range_unit and not units.same_unit(result.unit, range_unit):
        converted_value = units.convert(
            compare_value, result.unit, range_unit, result.canonical_name
        )
        if converted_value is None:
            notes.append(
                f"Unit mismatch: value unit '{result.unit}' differs from range unit "
                f"'{range_unit}' and no exact conversion is available; needs review."
            )
            return Analysis(STATUS_NEEDS_REVIEW, False, False, " ".join(dict.fromkeys(notes)))
        compare_value = converted_value
        compare_unit = range_unit
        converted = True
        notes.append(
            f"Compared after converting {result.value:g} {result.unit} to "
            f"{compare_value:.3g} {range_unit}; original value preserved."
        )

    if low is not None and compare_value < low:
        status = STATUS_LOW
    elif high is not None and compare_value > high:
        status = STATUS_HIGH
    else:
        status = STATUS_NORMAL

    critical_message = critical_values.evaluate(
        result.canonical_name, result.value, result.unit
    )
    if critical_message is None and converted:
        critical_message = critical_values.evaluate(
            result.canonical_name, compare_value, compare_unit
        )
    if critical_message:
        notes.append(critical_message)

    if result.report_flag:
        expected = {
            STATUS_LOW: "LOW",
            STATUS_HIGH: "HIGH",
            STATUS_NORMAL: "NORMAL",
        }.get(status, "")
        flag = result.report_flag.upper()
        flag_status = {
            "H": "HIGH", "HH": "HIGH", "HIGH": "HIGH",
            "L": "LOW", "LL": "LOW", "LOW": "LOW",
        }.get(flag, "")
        if flag_status and expected and flag_status != expected:
            notes.append(
                f"The report's printed flag ({flag}) does not match the computed "
                f"classification ({expected}); verify the extracted values."
            )

    return Analysis(
        status=status,
        critical_flag=bool(critical_message),
        unit_converted=converted,
        notes=" ".join(dict.fromkeys(n for n in notes if n)),
    )
