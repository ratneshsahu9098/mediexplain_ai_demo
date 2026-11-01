"""PDF text extraction with OCR fallback, using PyMuPDF."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pymupdf

from app.config import settings
from services import ocr_engine
from services.errors import ProcessingError

MIN_SELECTABLE_CHARS = 30


@dataclass
class PageText:
    page_number: int
    text: str
    used_ocr: bool


@dataclass
class PdfExtraction:
    pages: list[PageText]
    page_count: int
    method: str  # text | ocr | mixed


def extract_pdf(path: Path) -> PdfExtraction:
    try:
        document = pymupdf.open(path)
    except Exception as exc:
        raise ProcessingError(f"Could not open the PDF: {exc}") from exc

    try:
        page_count = document.page_count
        if page_count == 0:
            raise ProcessingError("The PDF contains no pages.")
        if page_count > settings.max_pdf_pages:
            raise ProcessingError(
                f"The PDF has {page_count} pages, which exceeds the "
                f"{settings.max_pdf_pages}-page limit."
            )

        pages: list[PageText] = []
        for index, page in enumerate(document):
            text = page.get_text("text") or ""
            if len(text.strip()) >= MIN_SELECTABLE_CHARS:
                pages.append(PageText(index + 1, text, False))
                continue

            # Image-only page: render and OCR it.
            pixmap = page.get_pixmap(dpi=settings.ocr_dpi, alpha=False)
            text = ocr_engine.image_bytes_to_text(pixmap.tobytes("png"))
            pages.append(PageText(index + 1, text, True))

        ocr_pages = sum(1 for p in pages if p.used_ocr)
        if ocr_pages == 0:
            method = "text"
        elif ocr_pages == len(pages):
            method = "ocr"
        else:
            method = "mixed"

        return PdfExtraction(pages=pages, page_count=page_count, method=method)
    finally:
        document.close()


def extract_image(path: Path) -> PdfExtraction:
    text = ocr_engine.image_file_to_text(path)
    return PdfExtraction(
        pages=[PageText(1, text, True)],
        page_count=1,
        method="ocr",
    )
