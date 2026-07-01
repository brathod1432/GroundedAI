"""Claim extraction module.

Responsible for splitting a generated answer into discrete, atomic
factual claims that can be individually verified against evidence.

In the current version this uses simple sentence-level splitting plus
keyword filtering. The design allows an LLM-powered extractor to be
swapped in later without changing the rest of the pipeline.
"""

from __future__ import annotations

import logging

from app.config import settings
from app.utils.text_utils import split_into_sentences, normalize_whitespace

logger = logging.getLogger(__name__)


def extract_claims(generated_answer: str) -> list[str]:
    """Extract factual claims from a generated answer.

    Strategy (v0.1 — rule-based):
        1. Split the answer into sentences.
        2. Filter out sentences that are too short or look non-factual
           (e.g. pure opinions without factual content).
        3. Normalize whitespace for clean output.
        4. Enforce the ``max_claims_per_answer`` cap from settings.

    Args:
        generated_answer: The full LLM-generated text to decompose.

    Returns:
        Ordered list of claim strings. Each claim is one sentence-length
        factual assertion.
    """
    sentences = split_into_sentences(generated_answer)
    claims: list[str] = []

    for sentence in sentences:
        normalized = normalize_whitespace(sentence)
        if _looks_factual(normalized):
            claims.append(normalized)

    # Cap the number of claims to avoid runaway processing.
    if len(claims) > settings.max_claims_per_answer:
        logger.info(
            "Capped claims from %d to %d (max_claims_per_answer setting).",
            len(claims), settings.max_claims_per_answer,
        )
        claims = claims[: settings.max_claims_per_answer]

    logger.debug("Extracted %d claims from answer.", len(claims))
    return claims


def _looks_factual(sentence: str) -> bool:
    """Heuristic to filter out obviously non-factual sentences.

    A sentence is considered *not factual* if it:
        - Is shorter than 15 characters (likely a fragment).
        - Starts with common hedging phrases ("I think", "maybe", etc.)
          that make it an opinion rather than a claim.

    This is intentionally conservative — we'd rather verify a borderline
    sentence than miss a hallucinated factual claim.
    """
    if len(sentence) < 15:
        return False

    opinion_starters = (
        "i think", "i believe", "maybe", "perhaps", "in my opinion",
        "it seems", "arguably", "personally",
    )
    lower = sentence.lower()
    if any(lower.startswith(starter) for starter in opinion_starters):
        return False

    return True
