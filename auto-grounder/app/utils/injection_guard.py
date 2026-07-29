"""Local minimal injection guard for the auto-grounder corrective prompt pipeline.

This is a lightweight version of the prompt-shield injection detector.
It catches the most dangerous injection patterns before they are embedded
into corrective prompts and forwarded to the LLM.
"""
from __future__ import annotations

import re
import unicodedata

_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(?:all\s+)?(?:previous|prior|above|earlier)\s+(?:instructions|prompts|rules|context)", re.IGNORECASE),
    re.compile(r"disregard\s+(?:all\s+)?(?:above|previous|prior|your)\s+(?:instructions|rules|guidelines)", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(?:DAN|jailbroken|unrestricted|unfiltered)", re.IGNORECASE),
    re.compile(r"pretend\s+(?:you\s+)?(?:are|have)\s+no\s+(?:restrictions|rules|limits|guidelines|ethics|filters)", re.IGNORECASE),
    re.compile(r"bypass\s+(?:safety|content|ethical|security)\s+(?:filters?|guidelines?|checks?|controls?)", re.IGNORECASE),
    re.compile(r"do\s+not\s+follow\s+(?:any\s+)?(?:rules|guidelines|instructions|policies)", re.IGNORECASE),
    re.compile(r"(?:reveal|show|print|output|repeat|display)\s+(?:your\s+)?(?:system\s+)?(?:prompt|instructions|rules)", re.IGNORECASE),
]

_ZERO_WIDTH = re.compile(r"[\u200b-\u200f\u202a-\u202e\ufeff\u2060]")


def _normalize(text: str) -> str:
    return _ZERO_WIDTH.sub("", unicodedata.normalize("NFKC", text))


def contains_injection(text: str) -> bool:
    """Return True if text appears to contain a prompt injection payload."""
    normalized = _normalize(text)
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(text) or pattern.search(normalized):
            return True
    return False
