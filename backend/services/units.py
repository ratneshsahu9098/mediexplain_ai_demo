"""Unit normalisation and safe, explicit unit conversion.

Conversion is only applied when the report's value unit differs from the
unit used by the report's own reference range and an exact factor is known.
The original value/unit are always preserved in the database.
"""

from __future__ import annotations

import re

# canonical display form keyed by a normalised lookup key
_CANONICAL_UNITS = {
    "g/dl": "g/dL",
    "g/l": "g/L",
    "gm/dl": "g/dL",
    "mg/dl": "mg/dL",
    "mg/l": "mg/L",
    "mmol/l": "mmol/L",
    "umol/l": "µmol/L",
    "ng/ml": "ng/mL",
    "ng/dl": "ng/dL",
    "pg/ml": "pg/mL",
    "pg/dl": "pg/dL",
    "nmol/l": "nmol/L",
    "pmol/l": "pmol/L",
    "miu/l": "mIU/L",
    "uiu/ml": "µIU/mL",
    "uiu/l": "µIU/L",
    "iu/l": "IU/L",
    "iu/ml": "IU/mL",
    "u/l": "U/L",
    "meq/l": "mEq/L",
    "mmol/24h": "mmol/24h",
    "/ul": "/µL",
    "/ul.": "/µL",
    "cells/ul": "cells/µL",
    "10^3/ul": "10^3/µL",
    "x10^3/ul": "x10^3/µL",
    "10*3/ul": "10^3/µL",
    "k/ul": "K/µL",
    "m/ul": "M/µL",
    "fl": "fL",
    "pg": "pg",
    "%": "%",
    "ml/min": "mL/min",
    "ml/min/1.73m2": "mL/min/1.73m²",
    "mm/hr": "mm/hr",
    "mm": "mm",
    "sec": "sec",
    "seconds": "sec",
    "ratio": "ratio",
    "index": "index",
}

# family used to look up conversion factors
_FAMILY = {
    "glucose": "glucose",
    "fasting_glucose": "glucose",
    "random_glucose": "glucose",
    "postprandial_glucose": "glucose",
    "total_cholesterol": "cholesterol",
    "ldl": "cholesterol",
    "vldl": "cholesterol",
    "triglycerides": "triglycerides",
    "creatinine": "creatinine",
    "bilirubin_total": "bilirubin",
    "bilirubin_direct": "bilirubin",
    "hemoglobin": "hemoglobin",
    "urea": "urea",
    "calcium": "calcium",
    "uric_acid": "uric_acid",
    "vitamin_d": "vitamin_d",
}

# multiply the value by the factor to move from `from` to `to`
_FACTORS: dict[tuple[str, str, str], float] = {
    ("glucose", "mg/dl", "mmol/l"): 1 / 18.0182,
    ("glucose", "mmol/l", "mg/dl"): 18.0182,
    ("cholesterol", "mg/dl", "mmol/l"): 1 / 38.67,
    ("cholesterol", "mmol/l", "mg/dl"): 38.67,
    ("triglycerides", "mg/dl", "mmol/l"): 1 / 88.57,
    ("triglycerides", "mmol/l", "mg/dl"): 88.57,
    ("creatinine", "mg/dl", "umol/l"): 88.4,
    ("creatinine", "umol/l", "mg/dl"): 1 / 88.4,
    ("bilirubin", "mg/dl", "umol/l"): 17.1,
    ("bilirubin", "umol/l", "mg/dl"): 1 / 17.1,
    ("hemoglobin", "g/dl", "g/l"): 10.0,
    ("hemoglobin", "g/l", "g/dl"): 0.1,
    ("urea", "mg/dl", "mmol/l"): 1 / 6.006,
    ("urea", "mmol/l", "mg/dl"): 6.006,
    ("calcium", "mg/dl", "mmol/l"): 0.2495,
    ("calcium", "mmol/l", "mg/dl"): 4.008,
    ("uric_acid", "mg/dl", "umol/l"): 59.48,
    ("uric_acid", "umol/l", "mg/dl"): 1 / 59.48,
    ("vitamin_d", "ng/ml", "nmol/l"): 2.496,
    ("vitamin_d", "nmol/l", "ng/ml"): 1 / 2.496,
}

# Units recognised in free text. Longest alternatives are tried first because
# the regex alternation is ordered.
UNIT_STRINGS: tuple[str, ...] = tuple(
    sorted(
        {
            "10^3/µL", "10^3/uL", "x10^3/µL", "x10^3/uL", "10*3/uL",
            "cells/µL", "cells/uL", "K/µL", "K/uL", "M/µL", "M/uL",
            "/µL", "/uL", "mL/min/1.73m²", "mL/min/1.73m2", "mL/min",
            "mmol/24h", "mm/hr", "mIU/L", "µIU/mL", "µIU/L", "uIU/mL",
            "IU/mL", "IU/L", "mEq/L", "mg/dL", "mg/L", "mg/dl", "mg/l",
            "g/dL", "g/L", "gm/dL", "gm/dl", "mmol/L", "µmol/L", "umol/L",
            "ng/mL", "ng/dL", "pg/mL", "pg/dL", "nmol/L", "pmol/L",
            "µg/dL", "ug/dL", "mcg/dL", "U/L", "u/L", "fL", "pg", "%",
            "mm", "sec", "seconds", "ratio", "index",
        },
        key=len,
        reverse=True,
    )
)


def _key(unit: str | None) -> str:
    if not unit:
        return ""
    value = unit.strip().lower()
    value = value.replace("μ", "u").replace("µ", "u")  # Greek mu / micro sign
    value = value.replace(" ", "")
    return value


def canonical_unit(unit: str | None) -> str:
    """Return the display form of a unit, or the trimmed original."""
    if not unit:
        return ""
    key = _key(unit)
    if key in _CANONICAL_UNITS:
        return _CANONICAL_UNITS[key]
    # tolerate trailing punctuation picked up from text
    trimmed = key.rstrip(".,;:")
    return _CANONICAL_UNITS.get(trimmed, unit.strip())


def unit_key(unit: str | None) -> str:
    return _key(unit)


def same_unit(a: str | None, b: str | None) -> bool:
    return _key(a) == _key(b)


def family_for(canonical: str | None) -> str | None:
    if not canonical:
        return None
    return _FAMILY.get(canonical)


def convert(value: float, from_unit: str, to_unit: str, canonical: str | None) -> float | None:
    """Return the converted value, or None when no exact conversion is known."""
    if same_unit(from_unit, to_unit):
        return value
    family = family_for(canonical)
    if not family:
        return None
    factor = _FACTORS.get((family, _key(from_unit), _key(to_unit)))
    if factor is None:
        return None
    return value * factor


def looks_like_unit(token: str) -> bool:
    return _key(token) in _CANONICAL_UNITS


def build_unit_pattern() -> re.Pattern[str]:
    alternatives = "|".join(re.escape(u) for u in UNIT_STRINGS)
    return re.compile(
        rf"(?<![A-Za-z])(?:{alternatives})(?![A-Za-z0-9])",
        re.IGNORECASE,
    )
