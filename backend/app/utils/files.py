"""Upload validation and private file storage helpers."""

from __future__ import annotations

import re
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, status

# extension -> (mime, signature check)
_SIGNATURES: dict[str, tuple[str, bytes]] = {
    ".pdf": ("application/pdf", b"%PDF"),
    ".jpg": ("image/jpeg", b"\xff\xd8\xff"),
    ".jpeg": ("image/jpeg", b"\xff\xd8\xff"),
    ".png": ("image/png", b"\x89PNG\r\n\x1a\n"),
}


def safe_original_name(filename: str | None) -> str:
    if not filename:
        return "report"
    name = Path(filename).name
    name = re.sub(r"[\x00-\x1f<>:\"/\\|?*]", "_", name).strip()
    return name[:255] or "report"


def validate_upload(filename: str | None, data: bytes) -> tuple[str, str]:
    """Validate extension + magic bytes. Returns (extension, mime_type)."""
    original = safe_original_name(filename)
    ext = Path(original).suffix.lower()
    if ext not in _SIGNATURES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported file type. Allowed: PDF, JPG, JPEG, PNG.",
        )
    if not data:
        raise HTTPException(status_code=422, detail="The uploaded file is empty.")

    mime, signature = _SIGNATURES[ext]
    if not data.startswith(signature):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="File content does not match its extension.",
        )
    return ext, mime


def store_upload(upload_root: Path, user_id: int, data: bytes, ext: str) -> Path:
    """Store a private upload under a per-user directory with a random name."""
    folder = upload_root / str(user_id)
    folder.mkdir(parents=True, exist_ok=True)
    destination = folder / f"{uuid4().hex}{ext}"
    destination.write_bytes(data)
    return destination
