"""Text processing utilities used across the pipeline.

Keeps text-manipulation logic out of business modules so they
stay focused on their core responsibility.
"""

from __future__ import annotations

import re


def split_into_sentences(text: str) -> list[str]:
    """Split text into sentences on period / question-mark / exclamation boundaries.

    This is intentionally simple — we avoid pulling in NLTK or spacy
    for the first version. Good enough for claim extraction where each
    sentence typically represents a distinct factual assertion.

    Args:
        text: The input text to split.

    Returns:
        A list of non-empty, stripped sentence strings.
    """
    # Split on sentence-ending punctuation followed by whitespace or end-of-string.
    raw = re.split(r'(?<=[.!?])\s+', text.strip())
    # Filter out empty strings and strip each piece.
    return [s.strip() for s in raw if s.strip()]


def normalize_whitespace(text: str) -> str:
    """Collapse multiple spaces/tabs/newlines into a single space."""
    return re.sub(r'\s+', ' ', text).strip()


def extract_keywords(text: str, min_length: int = 4) -> list[str]:
    """Extract lowercase keyword tokens longer than *min_length*.

    Removes common English stop-words so keyword matching in the
    verifier focuses on content words rather than grammar tokens.

    Args:
        text: Input text.
        min_length: Minimum token length to keep.

    Returns:
        Deduplicated list of keyword strings, lowercased.
    """
    stop_words: set[str] = {
        "that", "this", "with", "from", "have", "been", "were",
        "will", "would", "could", "should", "about", "which",
        "their", "there", "these", "those", "other", "some",
        "than", "into", "also", "just", "more", "very", "most",
        "such", "only", "over", "when", "what", "where", "while",
    }

    tokens = re.findall(r'[a-zA-Z]+', text.lower())
    seen: set[str] = set()
    keywords: list[str] = []
    for token in tokens:
        if len(token) >= min_length and token not in stop_words and token not in seen:
            seen.add(token)
            keywords.append(token)
    return keywords
