"""Toxicity and harmful content detection engine."""
from __future__ import annotations

import re
from dataclasses import dataclass

# Category patterns: each tuple is (category_name, compiled_pattern, weight)
_TOXICITY_CATEGORIES: list[tuple[str, re.Pattern[str], float]] = [
    (
        "hate_speech",
        re.compile(
            r"\b(?:kill\s+all|exterminate|genocide|ethnic\s+cleansing|"
            r"racial\s+(?:slur|superiority)|white\s+(?:supremac|power)|"
            r"death\s+to\s+(?:all)?)\b",
            re.IGNORECASE,
        ),
        0.95,
    ),
    (
        "violence_threats",
        re.compile(
            r"\b(?:(?:I\s+will|going\s+to|want\s+to|how\s+to)\s+"
            r"(?:kill|murder|harm|attack|assault|shoot|stab|bomb)|"
            r"instructions?\s+(?:to|for)\s+(?:making?\s+)?(?:a\s+)?(?:bomb|weapon|explosive))\b",
            re.IGNORECASE,
        ),
        0.95,
    ),
    (
        "self_harm",
        re.compile(
            r"\b(?:(?:how\s+to|ways?\s+to|methods?\s+(?:of|for))\s+"
            r"(?:kill\s+myself|suicide|self[- ]?harm|end\s+(?:my\s+)?life)|"
            r"suicide\s+(?:method|instruction|guide))\b",
            re.IGNORECASE,
        ),
        0.95,
    ),
    (
        "harassment",
        re.compile(
            r"\b(?:(?:write|generate|create)\s+(?:a\s+)?(?:harassing|threatening|abusive)\s+"
            r"(?:message|email|letter|text)|"
            r"(?:help\s+me\s+)?(?:bully|harass|stalk|threaten|dox|doxx)\s+(?:someone|a\s+person|them|him|her))\b",
            re.IGNORECASE,
        ),
        0.85,
    ),
    (
        "illegal_activity",
        re.compile(
            r"\b(?:(?:how\s+to|instructions?\s+(?:for|to)|steps?\s+to)\s+"
            r"(?:hack|break\s+into|steal|forge|counterfeit|launder|smuggle|"
            r"pick\s+a\s+lock|hotwire|synthesize\s+(?:drugs?|meth|fentanyl)))\b",
            re.IGNORECASE,
        ),
        0.80,
    ),
    (
        "profanity_severe",
        re.compile(
            r"\b(?:(?:you|they|he|she)\s+(?:are|is)\s+(?:a\s+)?(?:worthless|pathetic|disgusting)\s+"
            r"(?:piece\s+of|excuse\s+for))\b",
            re.IGNORECASE,
        ),
        0.60,
    ),
]


@dataclass
class ToxicityAnalysis:
    """Result of toxicity analysis."""
    is_toxic: bool
    toxicity_score: float
    flagged_categories: list[str]


def detect_toxicity(text: str, threshold: float = 0.7) -> ToxicityAnalysis:
    """Analyze text for toxic or harmful content.

    Returns a ToxicityAnalysis with a score based on the worst category
    matched. A text is classified as toxic if score >= threshold.
    """
    if not text or not text.strip():
        return ToxicityAnalysis(is_toxic=False, toxicity_score=0.0, flagged_categories=[])

    flagged: list[tuple[str, float]] = []
    for category, pattern, weight in _TOXICITY_CATEGORIES:
        if pattern.search(text):
            flagged.append((category, weight))

    if not flagged:
        return ToxicityAnalysis(is_toxic=False, toxicity_score=0.0, flagged_categories=[])

    score = max(w for _, w in flagged)
    if len(flagged) > 1:
        score = min(score + 0.05 * (len(flagged) - 1), 1.0)

    return ToxicityAnalysis(
        is_toxic=score >= threshold,
        toxicity_score=round(score, 2),
        flagged_categories=[cat for cat, _ in flagged],
    )
