"""Configurable critical-value thresholds.

IMPORTANT
---------
These thresholds are engineering placeholders for demonstration only. They
have NOT been clinically validated, are not exhaustive, and must not be used
to make real medical decisions. Before any real deployment, a qualified
clinician must review the thresholds, units, adult/paediatric differences and
the escalation text.
"""

from __future__ import annotations

from dataclasses import dataclass

from services.units import unit_key


@dataclass(frozen=True)
class CriticalRule:
    unit: str
    direction: str  # "below" | "above"
    threshold: float
    message: str


_LOW = "below"
_HIGH = "above"

CRITICAL_RULES: dict[str, tuple[CriticalRule, ...]] = {
    "hemoglobin": (
        CriticalRule("g/dL", _LOW, 7.0,
                     "This haemoglobin value is very low. Contact a healthcare professional urgently."),
        CriticalRule("g/L", _LOW, 70.0,
                     "This haemoglobin value is very low. Contact a healthcare professional urgently."),
        CriticalRule("g/dL", _HIGH, 20.0,
                     "This haemoglobin value is very high. Seek prompt medical advice."),
    ),
    "wbc": (
        CriticalRule("/µL", _LOW, 2000, "This white-cell count is very low. Seek urgent medical advice."),
        CriticalRule("/µL", _HIGH, 30000, "This white-cell count is very high. Seek urgent medical advice."),
        CriticalRule("10^3/µL", _LOW, 2.0, "This white-cell count is very low. Seek urgent medical advice."),
        CriticalRule("10^3/µL", _HIGH, 30.0, "This white-cell count is very high. Seek urgent medical advice."),
    ),
    "platelets": (
        CriticalRule("/µL", _LOW, 50000, "This platelet count is very low. Seek urgent medical advice."),
        CriticalRule("/µL", _HIGH, 1000000, "This platelet count is very high. Seek urgent medical advice."),
        CriticalRule("10^3/µL", _LOW, 50.0, "This platelet count is very low. Seek urgent medical advice."),
        CriticalRule("10^3/µL", _HIGH, 1000.0, "This platelet count is very high. Seek urgent medical advice."),
    ),
    "glucose": (
        CriticalRule("mg/dL", _LOW, 50, "This blood glucose value is very low. Seek urgent medical advice."),
        CriticalRule("mg/dL", _HIGH, 400, "This blood glucose value is very high. Seek urgent medical advice."),
        CriticalRule("mmol/L", _LOW, 2.8, "This blood glucose value is very low. Seek urgent medical advice."),
        CriticalRule("mmol/L", _HIGH, 22.2, "This blood glucose value is very high. Seek urgent medical advice."),
    ),
    "fasting_glucose": (
        CriticalRule("mg/dL", _LOW, 50, "This blood glucose value is very low. Seek urgent medical advice."),
        CriticalRule("mg/dL", _HIGH, 400, "This blood glucose value is very high. Seek urgent medical advice."),
        CriticalRule("mmol/L", _LOW, 2.8, "This blood glucose value is very low. Seek urgent medical advice."),
        CriticalRule("mmol/L", _HIGH, 22.2, "This blood glucose value is very high. Seek urgent medical advice."),
    ),
    "random_glucose": (
        CriticalRule("mg/dL", _LOW, 50, "This blood glucose value is very low. Seek urgent medical advice."),
        CriticalRule("mg/dL", _HIGH, 400, "This blood glucose value is very high. Seek urgent medical advice."),
        CriticalRule("mmol/L", _LOW, 2.8, "This blood glucose value is very low. Seek urgent medical advice."),
        CriticalRule("mmol/L", _HIGH, 22.2, "This blood glucose value is very high. Seek urgent medical advice."),
    ),
    "potassium": (
        CriticalRule("mEq/L", _LOW, 2.5, "This potassium value is very low. Seek urgent medical advice."),
        CriticalRule("mEq/L", _HIGH, 6.5, "This potassium value is very high. Seek urgent medical advice."),
        CriticalRule("mmol/L", _LOW, 2.5, "This potassium value is very low. Seek urgent medical advice."),
        CriticalRule("mmol/L", _HIGH, 6.5, "This potassium value is very high. Seek urgent medical advice."),
    ),
    "sodium": (
        CriticalRule("mEq/L", _LOW, 120, "This sodium value is very low. Seek urgent medical advice."),
        CriticalRule("mEq/L", _HIGH, 160, "This sodium value is very high. Seek urgent medical advice."),
        CriticalRule("mmol/L", _LOW, 120, "This sodium value is very low. Seek urgent medical advice."),
        CriticalRule("mmol/L", _HIGH, 160, "This sodium value is very high. Seek urgent medical advice."),
    ),
    "calcium": (
        CriticalRule("mg/dL", _LOW, 6.5, "This calcium value is very low. Seek urgent medical advice."),
        CriticalRule("mg/dL", _HIGH, 13.0, "This calcium value is very high. Seek urgent medical advice."),
    ),
}


def evaluate(canonical: str | None, value: float | None, unit: str) -> str | None:
    """Return an escalation message when a placeholder critical rule matches."""
    if canonical is None or value is None:
        return None
    rules = CRITICAL_RULES.get(canonical)
    if not rules:
        return None

    key = unit_key(unit)
    for rule in rules:
        if unit_key(rule.unit) != key:
            continue
        if rule.direction == _LOW and value < rule.threshold:
            return rule.message
        if rule.direction == _HIGH and value > rule.threshold:
            return rule.message
    return None
