from services.medical_analyzer import (
    STATUS_HIGH,
    STATUS_LOW,
    STATUS_NEEDS_REVIEW,
    STATUS_NORMAL,
    STATUS_NOT_AVAILABLE,
    STATUS_QUALITATIVE,
    STATUS_UNKNOWN,
    analyze_result,
)
from services.test_parser import ParsedResult


def make_result(**overrides) -> ParsedResult:
    defaults = dict(
        test_name="Hemoglobin",
        raw_name="Hemoglobin",
        canonical_name="hemoglobin",
        value=11.2,
        value_text="11.2",
        unit="g/dL",
        range_low=13.0,
        range_high=17.0,
        range_text="13 - 17",
        range_unit="",
    )
    defaults.update(overrides)
    return ParsedResult(**defaults)


def test_low_value():
    assert analyze_result(make_result(value=11.2)).status == STATUS_LOW


def test_normal_value():
    assert analyze_result(make_result(value=14.0)).status == STATUS_NORMAL


def test_high_value():
    assert analyze_result(make_result(value=18.5)).status == STATUS_HIGH


def test_boundaries_are_normal():
    assert analyze_result(make_result(value=13.0)).status == STATUS_NORMAL
    assert analyze_result(make_result(value=17.0)).status == STATUS_NORMAL


def test_missing_range_is_unknown():
    analysis = analyze_result(make_result(range_low=None, range_high=None, range_text=""))
    assert analysis.status == STATUS_UNKNOWN


def test_missing_value_is_not_available():
    analysis = analyze_result(make_result(value=None, value_text=""))
    assert analysis.status == STATUS_NOT_AVAILABLE


def test_qualitative_value():
    analysis = analyze_result(make_result(value=None, value_text="Negative", canonical_name="hbsag"))
    assert analysis.status == STATUS_QUALITATIVE


def test_unit_conversion_glucose():
    result = make_result(
        test_name="Blood Glucose",
        canonical_name="glucose",
        value=200,
        unit="mg/dL",
        range_low=4.0,
        range_high=7.0,
        range_text="4.0 - 7.0",
        range_unit="mmol/L",
    )
    analysis = analyze_result(result)
    assert analysis.status == STATUS_HIGH
    assert analysis.unit_converted is True
    assert "converting" in analysis.notes


def test_unit_conversion_hemoglobin():
    result = make_result(value=112, unit="g/L", range_unit="g/dL")
    analysis = analyze_result(result)
    assert analysis.status == STATUS_LOW
    assert analysis.unit_converted is True


def test_unknown_unit_conversion_needs_review():
    result = make_result(value=11.2, unit="mg/dL", range_unit="g/L")
    analysis = analyze_result(result)
    assert analysis.status == STATUS_NEEDS_REVIEW


def test_critical_flag():
    analysis = analyze_result(make_result(value=6.5))
    assert analysis.status == STATUS_LOW
    assert analysis.critical_flag is True
    assert "urgent" in analysis.notes.lower()


def test_printed_flag_conflict_is_noted():
    analysis = analyze_result(make_result(value=11.2, report_flag="H"))
    assert analysis.status == STATUS_LOW
    assert "does not match" in analysis.notes


def test_printed_flag_agreement_has_no_conflict_note():
    analysis = analyze_result(make_result(value=11.2, report_flag="L"))
    assert analysis.status == STATUS_LOW
    assert "does not match" not in analysis.notes
