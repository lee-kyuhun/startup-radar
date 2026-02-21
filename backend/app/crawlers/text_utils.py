from __future__ import annotations

import re

from bs4 import BeautifulSoup

_WHITESPACE_RE = re.compile(r"[ \t]+")
_NEWLINE_RE = re.compile(r"\n{2,}")

SUMMARY_MAX_LENGTH = 200


def strip_html(html: str) -> str:
    """Remove all HTML tags and return plain text."""
    soup = BeautifulSoup(html, "lxml")
    return soup.get_text(separator=" ")


def normalize_whitespace(text: str) -> str:
    """Collapse consecutive spaces/tabs and trim multiple blank lines."""
    text = _WHITESPACE_RE.sub(" ", text)
    text = _NEWLINE_RE.sub("\n", text)
    return text.strip()


def truncate_to_sentence(text: str, max_length: int = SUMMARY_MAX_LENGTH) -> str:
    """
    Truncate text to at most `max_length` characters, preferring to break
    at the last sentence boundary (period or newline) within that range.
    Falls back to a hard cut at `max_length` if no boundary is found.
    """
    if len(text) <= max_length:
        return text

    candidate = text[:max_length]

    # Look for the last period or newline within the candidate window
    last_period = candidate.rfind(".")
    last_newline = candidate.rfind("\n")
    boundary = max(last_period, last_newline)

    if boundary > 0:
        return candidate[: boundary + 1].rstrip()

    # Hard cut
    return candidate.rstrip()


def build_summary(raw: str | None) -> str | None:
    """
    Full pipeline:
    1. Strip HTML tags
    2. Normalize whitespace
    3. Truncate to SUMMARY_MAX_LENGTH at a sentence boundary
    4. Return None if the result is empty
    """
    if not raw:
        return None

    text = strip_html(raw)
    text = normalize_whitespace(text)

    if not text:
        return None

    return truncate_to_sentence(text)
