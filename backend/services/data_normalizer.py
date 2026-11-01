"""Text cleaning and normalisation for laboratory reports."""

from __future__ import annotations

import re
import unicodedata

_WHITESPACE_RE = re.compile(r"[ \t\u00a0\u2007\u202f]+")
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def _fix_separators(text: str) -> str:
    # thousands separators first: 7,500 or 1,234,567
    text = re.sub(r"(?<=\d),(?=\d{3}(?!\d))", "", text)
    # decimal comma: 11,2 -> 11.2
    text = re.sub(r"(?<=\d),(?=\d{1,2}(?!\d))", ".", text)
    return text


def normalize_line(line: str) -> str:
    line = unicodedata.normalize("NFKC", line)
    line = _CONTROL_RE.sub(" ", line)
    line = line.replace("\u00a0", " ").replace("\u2007", " ").replace("\u202f", " ")
    line = (
        line.replace("–", "-")
        .replace("—", "-")
        .replace("−", "-")
        .replace("‐", "-")
        .replace("≤", "<=")
        .replace("≥", ">=")
        .replace("×", "x")
    )
    line = _fix_separators(line)
    line = _WHITESPACE_RE.sub(" ", line)
    return line.strip()


def normalize_text(text: str) -> list[str]:
    """Normalise a block of text into non-empty lines."""
    if not text:
        return []
    lines: list[str] = []
    for raw in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = normalize_line(raw)
        if line:
            lines.append(line)
    return lines


def normalize_lookup(text: str) -> str:
    """Lowercase, punctuation-free form used for keyword checks."""
    text = unicodedata.normalize("NFKC", text).lower()
    text = text.replace("μ", "u").replace("µ", "u")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()
