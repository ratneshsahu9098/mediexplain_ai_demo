"""Table extraction with pdfplumber.

Table rows are flattened into a single line so the same line parser can be
used for both free text and tabular reports. Failures are non-fatal: text
extraction still provides a usable fallback.
"""

from __future__ import annotations

import re
from pathlib import Path

import pdfplumber

from app.config import settings

_EMPTY_CELL = re.compile(r"^\s*$")


def _clean_cell(value: object) -> str:
    if value is None:
        return ""
    text = str(value).replace("\n", " ").strip()
    return re.sub(r"\s{2,}", " ", text)


def extract_table_lines(path: Path) -> list[tuple[int, str]]:
    """Return (page_number, line) pairs from PDF tables."""
    rows: list[tuple[int, str]] = []
    try:
        with pdfplumber.open(path) as pdf:
            for index, page in enumerate(pdf.pages[: settings.max_pdf_pages]):
                try:
                    tables = page.extract_tables() or []
                except Exception:
                    continue
                for table in tables:
                    for row in table:
                        if not row:
                            continue
                        cells = [_clean_cell(cell) for cell in row]
                        cells = [cell for cell in cells if not _EMPTY_CELL.match(cell)]
                        if len(cells) < 2:
                            continue
                        line = " ".join(cells)
                        if not any(ch.isdigit() for ch in line):
                            continue
                        rows.append((index + 1, line))
    except Exception:
        # pdfplumber is best-effort; never fail the whole pipeline for tables.
        return rows
    return rows
