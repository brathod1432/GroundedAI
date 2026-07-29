"""Prompt injection and jailbreak detection engine.

SECURITY: Applies normalization before scanning to catch obfuscated attacks:
  - Unicode NFKC normalization catches homoglyph substitutions (е→e, і→i, etc.)
  - Zero-width character stripping removes invisible separator tricks.
  - Base64 blob decoding catches payloads encoded to bypass text filters.
  - Both the original and normalized forms are scanned; the worst score wins.
"""
from __future__ import annotations

import base64
import re
import unicodedata
from dataclasses import dataclass

# Regex to identify probable base64 blobs (at least 20 chars, typical padding)
_BASE64_BLOB = re.compile(r"[A-Za-z0-9+/]{20,}(?:={0,2})")

# Zero-width and invisible Unicode characters used to split keywords
_ZERO_WIDTH_CHARS = re.compile(
    r"[\u200b\u200c\u200d\u200e\u200f\u202a\u202b\u202c\u202d\u202e\ufeff\u2060]"
)


# Visual homoglyph mapping: characters that look like ASCII letters but are
# from other scripts (Cyrillic, Greek, etc.) and used in injection attacks.
# Maps non-ASCII Unicode code points to their ASCII visual equivalents.
_HOMOGLYPH_TABLE: dict[int, str] = {
    # Cyrillic
    0x0430: "a",  # а → a
    0x0435: "e",  # е → e
    0x043E: "o",  # о → o
    0x0440: "r",  # р → r
    0x0441: "c",  # с → c
    0x0443: "y",  # у → y
    0x0445: "x",  # х → x
    0x0456: "i",  # і → i
    0x0404: "E",  # Є → E
    0x0406: "I",  # І → I
    0x0410: "A",  # А → A
    0x0412: "B",  # В → B
    0x0415: "E",  # Е → E
    0x041A: "K",  # К → K
    0x041C: "M",  # М → M
    0x041D: "H",  # Н → H
    0x041E: "O",  # О → O
    0x0420: "P",  # Р → P
    0x0421: "C",  # С → C
    0x0422: "T",  # Т → T
    0x0425: "X",  # Х → X
    # Greek
    0x03B1: "a",  # α → a
    0x03BF: "o",  # ο → o
    0x03C1: "p",  # ρ → p
    0x03B9: "i",  # ι → i
    0x03BA: "k",  # κ → k
}
_HOMOGLYPH_TRANS = str.maketrans(_HOMOGLYPH_TABLE)


def _normalize_for_scan(text: str) -> str:
    """Return a normalized version of *text* for injection scanning.

    Performs four passes:
    1. NFKC normalization — collapses compatibility characters.
    2. Confusables mapping — replaces visual homoglyphs (Cyrillic, Greek)
       with their ASCII equivalents (catches е→e, і→i, etc.).
    3. Zero-width character removal — removes invisible separators used to
       split injection keywords (e.g., ``ig​nore`` → ``ignore``).
    4. Base64 decoding — any blob that successfully decodes to ASCII is
       appended so its plain-text content is also scanned.
    """
    # Pass 1: unicode normalization
    normalized = unicodedata.normalize("NFKC", text)

    # Pass 2: visual homoglyph replacement
    normalized = normalized.translate(_HOMOGLYPH_TRANS)

    # Pass 3: strip zero-width chars
    normalized = _ZERO_WIDTH_CHARS.sub("", normalized)

    # Pass 4: attempt to decode base64 blobs and append decoded content
    extra_parts: list[str] = []
    for blob in _BASE64_BLOB.findall(normalized):
        # Add padding if necessary before decoding
        padded = blob + "=" * ((4 - len(blob) % 4) % 4)
        try:
            decoded = base64.b64decode(padded).decode("utf-8", errors="ignore")
            # Only append if the decoded text contains printable ASCII content
            if decoded.isprintable() and len(decoded) >= 10:
                extra_parts.append(decoded)
        except Exception:
            pass

    if extra_parts:
        normalized = normalized + " " + " ".join(extra_parts)

    return normalized

# Each pattern has a name, regex, and weight (contribution to risk score)
_INJECTION_RULES: list[tuple[str, re.Pattern[str], float]] = [
    (
        "ignore_previous_instructions",
        re.compile(r"ignore\s+(?:all\s+)?(?:previous|prior|above|earlier)\s+(?:instructions|prompts|rules|context)", re.IGNORECASE),
        0.95,
    ),
    (
        "disregard_instructions",
        re.compile(r"disregard\s+(?:all\s+)?(?:above|previous|prior|your)\s+(?:instructions|rules|guidelines)", re.IGNORECASE),
        0.95,
    ),
    (
        "role_override_dan",
        re.compile(r"you\s+are\s+now\s+(?:DAN|jailbroken|unrestricted|unfiltered)", re.IGNORECASE),
        0.90,
    ),
    (
        "pretend_no_restrictions",
        re.compile(r"pretend\s+(?:you\s+)?(?:are|have)\s+no\s+(?:restrictions|rules|limits|guidelines|ethics|filters)", re.IGNORECASE),
        0.90,
    ),
    (
        "bypass_safety",
        re.compile(r"bypass\s+(?:safety|content|ethical|security)\s+(?:filters?|guidelines?|checks?|controls?)", re.IGNORECASE),
        0.90,
    ),
    (
        "do_anything_now",
        re.compile(r"(?:do\s+anything\s+now|DAN\s+mode|developer\s+mode\s+enabled)", re.IGNORECASE),
        0.85,
    ),
    (
        "system_prompt_override",
        re.compile(r"(?:^|\n)\s*(?:system\s*:|SYSTEM\s*:|###\s*(?:system|instruction|override)\s*:)", re.IGNORECASE),
        0.80,
    ),
    (
        "delimiter_injection",
        re.compile(r"(?:```\s*system|<\|(?:im_start|system)\|>|</?system>)", re.IGNORECASE),
        0.80,
    ),
    (
        "instruction_leak_request",
        re.compile(r"(?:reveal|show|print|output|repeat|display)\s+(?:your\s+)?(?:system\s+)?(?:prompt|instructions|rules)", re.IGNORECASE),
        0.70,
    ),
    (
        "roleplay_unrestricted",
        re.compile(r"(?:act|behave|respond)\s+(?:as\s+(?:if|though)\s+)?(?:you\s+)?(?:have\s+)?(?:no|without)\s+(?:restrictions|limits|rules|filters)", re.IGNORECASE),
        0.75,
    ),
    (
        "base64_injection",
        re.compile(r"(?:decode|interpret|execute|follow)\s+(?:this\s+)?(?:base64|encoded|b64)", re.IGNORECASE),
        0.70,
    ),
    (
        "do_not_follow_rules",
        re.compile(r"do\s+not\s+follow\s+(?:any\s+)?(?:rules|guidelines|instructions|policies)", re.IGNORECASE),
        0.85,
    ),
]


@dataclass
class InjectionAnalysis:
    """Result of injection detection."""
    is_injection: bool
    risk_score: float
    matched_patterns: list[str]


@dataclass
class _MatchDetail:
    rule_name: str
    matched_text: str
    weight: float


def _scan_text(text: str) -> list[_MatchDetail]:
    """Run all injection rules against *text* and return matched details."""
    matched: list[_MatchDetail] = []
    for rule_name, pattern, weight in _INJECTION_RULES:
        if pattern.search(text):
            matched.append(_MatchDetail(rule_name=rule_name, matched_text=pattern.pattern, weight=weight))
    return matched


def detect_injection(text: str, threshold: float = 0.7) -> InjectionAnalysis:
    """Analyze text for prompt injection patterns.

    Scans both the raw text AND a normalized form (NFKC + zero-width strip +
    base64 decoding) so that obfuscated injection payloads are caught.

    The risk score is the maximum weight among all matched patterns.
    A text is classified as injection if risk_score >= threshold.
    """
    if not text or not text.strip():
        return InjectionAnalysis(is_injection=False, risk_score=0.0, matched_patterns=[])

    # Scan the original text
    matched_raw = _scan_text(text)

    # Scan the normalized form (catches obfuscated/encoded attacks)
    normalized = _normalize_for_scan(text)
    matched_norm = _scan_text(normalized) if normalized != text else []

    # Merge: collect all unique rule names that matched either form
    seen_rules: set[str] = set()
    matched: list[_MatchDetail] = []
    for detail in matched_raw + matched_norm:
        if detail.rule_name not in seen_rules:
            seen_rules.add(detail.rule_name)
            matched.append(detail)

    if not matched:
        return InjectionAnalysis(is_injection=False, risk_score=0.0, matched_patterns=[])

    risk_score = max(m.weight for m in matched)
    # Boost score slightly when multiple patterns match (capped at 1.0)
    if len(matched) > 1:
        risk_score = min(risk_score + 0.05 * (len(matched) - 1), 1.0)

    return InjectionAnalysis(
        is_injection=risk_score >= threshold,
        risk_score=round(risk_score, 2),
        matched_patterns=[m.rule_name for m in matched],
    )
