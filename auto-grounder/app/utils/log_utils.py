"""Safe logging utilities for Auto-Grounder.

See truthguard-ai/app/utils/log_utils.py for full rationale.
"""

from __future__ import annotations

import hashlib
import re

_UNSAFE_LOG_CHARS = re.compile(r"[\r\n\x1b\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def safe_preview(text: str, max_chars: int = 60) -> str:
    """Return a sanitized, truncated preview of *text* safe for log lines."""
    sanitized = _UNSAFE_LOG_CHARS.sub(" ", text)
    sanitized = " ".join(sanitized.split())
    if len(sanitized) > max_chars:
        return sanitized[:max_chars] + "…"
    return sanitized


def content_hash(text: str) -> str:
    """Return a short SHA-256 identifier for a piece of content."""
    digest = hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()
    return f"sha:{digest[:12]}"
