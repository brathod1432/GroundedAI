"""PII scrubbing and re-injection engine."""
from __future__ import annotations

from dataclasses import dataclass, field

from app.core.pii_detector import PIIMatch, detect_pii


@dataclass
class ScrubResult:
    """Result of PII scrubbing."""
    sanitized_text: str
    pii_mapping: dict[str, str]  # placeholder -> original value
    matches: list[PIIMatch]


def _make_placeholder(pii_type: str, index: int) -> str:
    """Generate a deterministic placeholder like [EMAIL_1], [PHONE_2]."""
    return f"[{pii_type.upper()}_{index}]"


def scrub_pii(text: str) -> ScrubResult:
    """Detect and replace all PII in text with placeholders.

    Returns a ScrubResult with the sanitized text and a mapping
    that can be used to restore the original values.
    """
    matches = detect_pii(text)
    if not matches:
        return ScrubResult(sanitized_text=text, pii_mapping={}, matches=[])

    # Assign sequential placeholders per type
    type_counters: dict[str, int] = {}
    placeholders: list[tuple[PIIMatch, str]] = []
    for match in matches:
        count = type_counters.get(match.pii_type, 0) + 1
        type_counters[match.pii_type] = count
        placeholder = _make_placeholder(match.pii_type, count)
        placeholders.append((match, placeholder))

    # Build sanitized text by replacing from end to start (preserves positions)
    sanitized = text
    pii_mapping: dict[str, str] = {}
    for match, placeholder in reversed(placeholders):
        sanitized = sanitized[:match.start] + placeholder + sanitized[match.end:]
        pii_mapping[placeholder] = match.value

    return ScrubResult(sanitized_text=sanitized, pii_mapping=pii_mapping, matches=matches)


def restore_pii(sanitized_text: str, pii_mapping: dict[str, str]) -> str:
    """Re-inject original PII values back into text using the mapping."""
    result = sanitized_text
    for placeholder, original in pii_mapping.items():
        result = result.replace(placeholder, original)
    return result
