"""Logging utilities for safe user-content logging.

SECURITY NOTE: Never log raw user-supplied content. User input may contain
PII (emails, SSNs, phone numbers), injection payloads, or log-injection
attack strings (CRLF, ANSI escape sequences).  Use these helpers to produce
safe log tokens that help with debugging without exposing sensitive data.
"""

from __future__ import annotations

import hashlib
import re

# Characters that should never appear in log lines from user content.
# Newlines enable log-injection; ANSI codes can pollute log renderers.
_UNSAFE_LOG_CHARS = re.compile(r"[\r\n\x1b\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def safe_preview(text: str, max_chars: int = 60) -> str:
    """Return a sanitized, truncated preview of *text* safe for log lines.

    Steps:
        1. Strip control characters and ANSI escape codes.
        2. Collapse internal whitespace to single spaces.
        3. Truncate to *max_chars* and append ``…`` if longer.

    Args:
        text: Raw user-supplied text that may contain unsafe characters.
        max_chars: Maximum characters to include in the preview (default 60).

    Returns:
        A single-line, printable string safe for log output.
    """
    sanitized = _UNSAFE_LOG_CHARS.sub(" ", text)
    sanitized = " ".join(sanitized.split())  # collapse whitespace
    if len(sanitized) > max_chars:
        return sanitized[:max_chars] + "…"
    return sanitized


def content_hash(text: str) -> str:
    """Return a short SHA-256 prefix that identifies a piece of text.

    Useful when you need a stable, non-reversible identifier in logs
    (e.g., for correlating requests without logging the actual content).

    Returns:
        First 12 hex characters of the SHA-256 digest, prefixed with ``sha:``.
    """
    digest = hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()
    return f"sha:{digest[:12]}"
