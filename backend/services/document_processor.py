"""Orchestrates document text extraction and structured result parsing."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from services import pdf_extractor, table_extractor
from services.data_normalizer import normalize_text
from services.errors import ProcessingError
from services.test_catalog import detect_report_type
from services.test_parser import ParsedResult, deduplicate, parse_line, parse_lines


@dataclass
class DocumentResult:
    results: list[ParsedResult]
    report_type: str
    extraction_method: str
    page_count: int
    warning: str = ""
    canonicals: set[str] = field(default_factory=set)


def process_document(path: Path, extension: str) -> DocumentResult:
    ext = extension.lower()
    if ext == ".pdf":
        extraction = pdf_extractor.extract_pdf(path)
        table_lines = table_extractor.extract_table_lines(path)
    elif ext in {".jpg", ".jpeg", ".png"}:
        extraction = pdf_extractor.extract_image(path)
        table_lines = []
    else:
        raise ProcessingError(f"Unsupported document type: {extension}")

    parsed: list[ParsedResult] = []
    for page in extraction.pages:
        lines = normalize_text(page.text)
        parsed.extend(parse_lines(lines, page=page.page_number))

    # Table rows are parsed independently: merging across rows would be wrong.
    for page_number, row in table_lines:
        normalized = normalize_text(row)
        if not normalized:
            continue
        result = parse_line(normalized[0], page=page_number)
        if result is not None:
            result.notes.append("Extracted from a table row.")
            parsed.append(result)

    results = deduplicate(parsed)
    canonicals = {
        result.canonical_name
        for result in results
        if result.canonical_name is not None
    }

    warning = ""
    if not results:
        warning = (
            "No laboratory results could be extracted automatically. The layout may "
            "be unsupported or the scan may be unclear. Please check the original report."
        )

    return DocumentResult(
        results=results,
        report_type=detect_report_type(canonicals),
        extraction_method=extraction.method,
        page_count=extraction.page_count,
        warning=warning,
        canonicals=canonicals,
    )
