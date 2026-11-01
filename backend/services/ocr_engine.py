"""Tesseract OCR wrapper with availability detection and basic pre-processing."""

from __future__ import annotations

import shutil
from functools import lru_cache
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps

from app.config import settings
from services.errors import OcrUnavailableError

try:  # pragma: no cover - import guard only
    import pytesseract
except Exception:  # pragma: no cover
    pytesseract = None  # type: ignore[assignment]

_WINDOWS_CANDIDATES = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
)


@lru_cache
def _resolve_tesseract() -> str | None:
    if settings.tesseract_cmd:
        candidate = Path(settings.tesseract_cmd)
        if candidate.exists():
            return str(candidate)
    found = shutil.which("tesseract")
    if found:
        return found
    for candidate in _WINDOWS_CANDIDATES:
        if Path(candidate).exists():
            return candidate
    return None


def is_available() -> bool:
    if pytesseract is None:
        return False
    path = _resolve_tesseract()
    if not path:
        return False
    pytesseract.pytesseract.tesseract_cmd = path
    return True


def _prepare(image: Image.Image) -> Image.Image:
    image = image.convert("L")
    image = ImageOps.autocontrast(image)
    # Upscale small images; Tesseract does poorly on tiny text.
    width, height = image.size
    if width < 1200:
        scale = 1200 / max(width, 1)
        image = image.resize((int(width * scale), int(height * scale)), Image.LANCZOS)
    return image


def image_to_text(image: Image.Image) -> str:
    if not is_available():
        raise OcrUnavailableError(
            "This report appears to be scanned, and Tesseract OCR is not available. "
            "Install Tesseract and set TESSERACT_CMD, or upload a PDF with selectable text."
        )
    prepared = _prepare(image)
    try:
        return pytesseract.image_to_string(prepared, lang="eng")
    except Exception as exc:  # pragma: no cover - depends on local install
        raise OcrUnavailableError(f"OCR failed: {exc}") from exc


def image_bytes_to_text(data: bytes) -> str:
    with Image.open(BytesIO(data)) as image:
        return image_to_text(image)


def image_file_to_text(path: Path) -> str:
    with Image.open(path) as image:
        return image_to_text(image)
