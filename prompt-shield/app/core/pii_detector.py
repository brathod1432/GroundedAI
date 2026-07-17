"""PII detection engine using regex pattern matching."""
from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class PIIMatch:
    """A single PII match found in text."""
    pii_type: str
    value: str
    start: int
    end: int


# Patterns ordered from most specific to least specific to avoid partial matches
PII_PATTERNS: dict[str, re.Pattern[str]] = {
    "api_key": re.compile(
        r"\b(?:sk-[a-zA-Z0-9]{20,}|sk-proj-[a-zA-Z0-9_-]{20,}|AKIA[A-Z0-9]{16}|ghp_[a-zA-Z0-9]{36}|glpat-[a-zA-Z0-9\-_]{20,})\b"
    ),
    "email": re.compile(
        r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"
    ),
    "ssn": re.compile(
        r"\b\d{3}[-\s]\d{2}[-\s]\d{4}\b"
    ),
    "credit_card": re.compile(
        r"\b(?:\d{4}[-\s]){3}\d{4}\b"
    ),
    "phone": re.compile(
        r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
    ),
    "ip_address": re.compile(
        r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"
    ),
}


def detect_pii(text: str) -> list[PIIMatch]:
    """Scan text for PII entities and return all matches.
    
    Returns matches sorted by start position. Overlapping matches
    are resolved by keeping the first (most specific) match.
    """
    matches: list[PIIMatch] = []
    occupied: set[int] = set()  # track character positions already claimed
    
    for pii_type, pattern in PII_PATTERNS.items():
        for m in pattern.finditer(text):
            # Skip if this region overlaps with an already-claimed match
            span = set(range(m.start(), m.end()))
            if span & occupied:
                continue
            occupied.update(span)
            matches.append(PIIMatch(
                pii_type=pii_type,
                value=m.group(),
                start=m.start(),
                end=m.end(),
            ))
    
    matches.sort(key=lambda x: x.start)
    return matches
