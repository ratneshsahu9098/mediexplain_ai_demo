"""Shared schema helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from pydantic import BeforeValidator

__all__ = ["UTCDateTime"]


def _ensure_utc(value: object) -> object:
    """Treat naive datetimes as UTC.

    SQLite (and some other drivers) return timezone-naive values even for
    ``DateTime(timezone=True)`` columns. The values were written as UTC, so
    attaching ``timezone.utc`` before serialisation keeps the ISO string
    correct (``...Z`` / ``+00:00``) and lets the browser convert to local time.
    """
    if isinstance(value, datetime) and value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


UTCDateTime = Annotated[datetime, BeforeValidator(_ensure_utc)]
