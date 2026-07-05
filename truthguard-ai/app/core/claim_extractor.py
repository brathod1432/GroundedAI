"""Claim extraction module.

Responsible for splitting a generated answer into discrete, atomic
factual claims that can be individually verified against evidence.

In the current version this uses rule-based sentence splitting with
pattern-based factuality detection. The design allows an LLM-powered
extractor to be swapped in later without changing the rest of the pipeline.
"""

from __future__ import annotations

import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.config import settings
from app.utils.text_utils import split_into_sentences, normalize_whitespace

logger = logging.getLogger(__name__)

# Patterns that indicate factual content
_FACTUAL_PATTERNS = [
    r"\b(is|are|was|were|has|have|had)\b",          # copula/possession
    r"\b(was|were)\s+\w+ed\b",                       # passive voice
    r"\b\d+(?:,\d{3})*(?:\.\d+)?\s*(?:%|percent|million|billion|thousand)\b",  # statistics
    r"\b(in|on|at|by|from|to|of)\s+\d{4}\b",       # dates
    r"\baccording to\b",                              # attribution
    r"\b(study|research|report|data|survey)\s+(?:shows?|found|indicates?)\b",  # evidence claims
    r"\b(?:capital|population|GDP|revenue|area|height|weight)\b",  # common entities
]

# Patterns that indicate non-factual content
_NON_FACTUAL_PATTERNS = [
    r"^(i think|i believe|i feel|in my opinion|personally|arguably|maybe|perhaps)\b",
    r"^(it seems|it appears|it looks like|presumably|supposedly)\b",
    r"^(you should|we should|one should|consider|try|recommend)\b",
]


@dataclass
class ExtractedClaim:
    """A single extracted claim with metadata."""
    text: str
    claim_type: str = "factual"  # factual, statistical, causal, definitional
    confidence: float = 1.0
    start_index: int = 0
    end_index: int = 0


class BaseClaimExtractor(ABC):
    """Abstract interface for claim extraction backends."""

    @abstractmethod
    def extract(self, text: str) -> list[ExtractedClaim]:
        """Extract factual claims from text.

        Args:
            text: The input text to extract claims from.

        Returns:
            List of ExtractedClaim objects with text, type, confidence, and position.
        """
        raise NotImplementedError


class RuleBasedClaimExtractor(BaseClaimExtractor):
    """Rule-based claim extractor using pattern matching.

    This is the default v0.1 extractor. It uses regex patterns to identify
    factual sentences and filter out opinions/hedging.
    """

    def extract(self, text: str) -> list[ExtractedClaim]:
        """Extract factual claims using rule-based heuristics."""
        # Initial sentence split
        sentences = split_into_sentences(text)

        # Further split on strong conjunctions that separate claims
        split_sentences = []
        for s in sentences:
            parts = re.split(r"\s+(?:but|however|while|although|whereas)\s+", s, flags=re.IGNORECASE)
            for part in parts:
                part = part.strip()
                if part:
                    split_sentences.append(part)

        claims: list[ExtractedClaim] = []
        current_pos = 0

        for sentence in split_sentences:
            normalized = normalize_whitespace(sentence)
            if _looks_factual(normalized):
                claim_type = _classify_claim_type(normalized)
                claims.append(ExtractedClaim(
                    text=normalized,
                    claim_type=claim_type,
                    confidence=0.85,
                    start_index=current_pos,
                    end_index=current_pos + len(normalized),
                ))
            current_pos += len(sentence) + 1  # +1 for space/punctuation

        # Cap the number of claims
        if len(claims) > settings.max_claims_per_answer:
            logger.info(
                "Capped claims from %d to %d (max_claims_per_answer setting).",
                len(claims), settings.max_claims_per_answer,
            )
            claims = claims[: settings.max_claims_per_answer]

        logger.debug("Extracted %d claims from answer.", len(claims))
        return claims


class LLMClaimExtractor(BaseClaimExtractor):
    """LLM-based claim extractor (stub for future implementation).

    This extractor would use an LLM to decompose text into atomic claims
    with structured output (claim type, confidence, entities, etc.).

    Example prompt structure:
        "Extract all factual claims from the following text. Return as JSON:
         [{\"text\": \"...\", \"type\": \"statistical|causal|factual|definitional\",
           \"confidence\": 0.9, \"entities\": [\"...\"]}]"
    """

    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        if llm_client is None:
            logger.warning("LLMClaimExtractor initialized without LLM client - using mock mode")

    def extract(self, text: str) -> list[ExtractedClaim]:
        """Extract claims using LLM (stub implementation)."""
        # TODO: Implement with actual LLM call when available
        # For now, fall back to rule-based
        logger.info("LLMClaimExtractor: falling back to rule-based extraction")
        fallback = RuleBasedClaimExtractor()
        return fallback.extract(text)


def extract_claims(generated_answer: str) -> list[str]:
    """Extract factual claims from a generated answer.

    Strategy (v0.1 — rule-based):
        1. Split the answer into sentences.
        2. Split compound sentences on conjunctions (but, however, while).
        3. Filter out sentences that are too short or look non-factual.
        4. Score remaining sentences for factuality.
        5. Normalize whitespace for clean output.
        6. Enforce the ``max_claims_per_answer`` cap from settings.

    Args:
        generated_answer: The full LLM-generated text to decompose.

    Returns:
        Ordered list of claim strings. Each claim is one sentence-length
        factual assertion.
    """
    extractor = RuleBasedClaimExtractor()
    extracted = extractor.extract(generated_answer)
    return [c.text for c in extracted]


def _classify_claim_type(text: str) -> str:
    """Classify the type of claim based on content patterns."""
    lower = text.lower()
    if re.search(r"\b\d+(?:,\d{3})*(?:\.\d+)?\s*(?:%|percent|million|billion|thousand)\b", lower):
        return "statistical"
    if re.search(r"\b(causes?|leads? to|results? in|due to|because)\b", lower):
        return "causal"
    if re.search(r"\b(is|are|means?|refers to|defined as)\b", lower):
        return "definitional"
    return "factual"


def _looks_factual(sentence: str) -> bool:
    """Heuristic to filter out obviously non-factual sentences.

    A sentence is considered *not factual* if it:
        - Is shorter than 15 characters (likely a fragment).
        - Starts with opinion/hedging phrases.
        - Is purely imperative or conversational.

    A sentence is considered *factual* if it:
        - Contains copula/possession verbs (is, has, was, etc.)
        - Contains statistics, dates, or entity references
        - Attributes information to a source

    This is intentionally conservative — we'd rather verify a borderline
    sentence than miss a hallucinated factual claim.
    """
    if len(sentence) < 15:
        return False

    lower = sentence.lower()

    # Quick reject: non-factual starters
    for pattern in _NON_FACTUAL_PATTERNS:
        if re.search(pattern, lower):
            return False

    # Positive signals: factual patterns
    for pattern in _FACTUAL_PATTERNS:
        if re.search(pattern, lower):
            return True

    # Default: if it has a verb-like structure, consider it potentially factual
    # Check for subject-verb pattern (simple heuristic)
    words = lower.split()
    if len(words) >= 4:
        # Has some structure, might be factual
        return True

    return False
