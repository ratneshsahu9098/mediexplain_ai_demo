from services.data_normalizer import normalize_line, normalize_text
from services.test_parser import parse_line, parse_lines


def test_parses_standard_cbc_line():
    result = parse_line("Hemoglobin 11.2 g/dL 13 - 17")
    assert result is not None
    assert result.canonical_name == "hemoglobin"
    assert result.test_name == "Hemoglobin"
    assert result.value == 11.2
    assert result.unit == "g/dL"
    assert result.range_low == 13.0
    assert result.range_high == 17.0
    assert result.confidence >= 0.9


def test_parses_thousands_separator():
    result = parse_line("WBC 7,500 /uL 4,000 - 11,000")
    assert result is not None
    assert result.value == 7500
    assert result.range_low == 4000
    assert result.range_high == 11000
    assert result.unit == "/µL"


def test_decimal_comma_is_normalised():
    assert normalize_line("Hemoglobin 11,2 g/dL 13,0 - 17,0") == "Hemoglobin 11.2 g/dL 13.0 - 17.0"


def test_upper_bound_only_range():
    result = parse_line("Total Cholesterol 220 mg/dL < 200")
    assert result is not None
    assert result.value == 220
    assert result.range_low is None
    assert result.range_high == 200


def test_lower_bound_only_range():
    result = parse_line("HDL Cholesterol 35 mg/dL > 40")
    assert result is not None
    assert result.value == 35
    assert result.range_low == 40
    assert result.range_high is None


def test_missing_range_produces_note_and_lower_confidence():
    result = parse_line("Serum Creatinine 1.1 mg/dL")
    assert result is not None
    assert result.range_low is None
    assert result.range_high is None
    assert any("No reference range" in note for note in result.notes)
    assert result.confidence < 0.9


def test_qualitative_result():
    result = parse_line("HBsAg Negative")
    assert result is not None
    assert result.canonical_name == "hbsag"
    assert result.value is None
    assert result.value_text == "Negative"


def test_trailing_flag_is_captured():
    result = parse_line("Hemoglobin 10.2 g/dL 13 - 17 L")
    assert result is not None
    assert result.value == 10.2
    assert result.report_flag == "L"


def test_two_units_are_associated_with_value_and_range():
    result = parse_line("Fasting Blood Sugar 200 mg/dL 4.0 - 7.0 mmol/L")
    assert result is not None
    assert result.value == 200
    assert result.unit == "mg/dL"
    assert result.range_unit == "mmol/L"
    assert result.range_low == 4.0
    assert result.range_high == 7.0


def test_name_and_value_on_separate_lines():
    results = parse_lines(["Hemoglobin", "11.2 g/dL 13 - 17"])
    assert len(results) == 1
    assert results[0].value == 11.2
    assert results[0].range_low == 13


def test_dates_and_headers_are_ignored():
    lines = ["Patient Name: John Doe", "Date 01/02/2026", "Hemoglobin 11.2 g/dL 13-17"]
    assert parse_line(lines[0]) is None
    assert parse_line(lines[1]) is None
    assert parse_line(lines[2]) is not None


def test_unknown_test_still_extracted():
    result = parse_line("Some Special Assay 4.2 mg/L 1.0 - 5.0")
    assert result is not None
    assert result.canonical_name is None
    assert result.test_name == "Some Special Assay"
    assert result.value == 4.2


def test_serial_number_prefix_removed():
    result = parse_line("1. Hemoglobin 11.2 g/dL 13 - 17")
    assert result is not None
    assert result.raw_name == "Hemoglobin"


def test_normalize_text_drops_empty_lines():
    lines = normalize_text("A\n\n   \nB")
    assert lines == ["A", "B"]
