"""Unit tests for claim_extractor module."""

from app.core.claim_extractor import extract_claims, _looks_factual


class TestLooksFactual:
    """Tests for the _looks_factual heuristic filter."""

    def test_short_sentence_is_not_factual(self) -> None:
        assert _looks_factual("Too short.") is False

    def test_opinion_starter_is_not_factual(self) -> None:
        assert _looks_factual("I think the sky is blue and that is a fact.") is False

    def test_factual_sentence_passes(self) -> None:
        assert _looks_factual("The population of France is 68 million.") is True

    def test_hedging_maybe_is_not_factual(self) -> None:
        assert _looks_factual("Maybe the earth is round, but who really knows?") is False

    def test_minimum_length_boundary(self) -> None:
        # Exactly 15 chars: "The sky is blue" = 15
        assert _looks_factual("The sky is blueX") is True  # 16 chars, factual

    def test_maybe_starter(self) -> None:
        assert _looks_factual("Maybe this is a factual claim about something.") is False


class TestExtractClaims:
    """Tests for the main extract_claims function."""

    def test_splits_into_sentences(self) -> None:
        answer = "France has 68 million people. Paris is the capital city."
        claims = extract_claims(answer)
        assert len(claims) == 2
        assert "France has 68 million people." in claims

    def test_filters_short_fragments(self) -> None:
        answer = "Yes. France has 68 million people as of 2023."
        claims = extract_claims(answer)
        # "Yes." is 4 chars → filtered out
        assert all(len(c) >= 15 for c in claims)

    def test_filters_opinion_sentences(self) -> None:
        answer = "I think this is correct. The population is 68 million."
        claims = extract_claims(answer)
        assert len(claims) == 1
        assert "population" in claims[0].lower()

    def test_empty_input(self) -> None:
        assert extract_claims("") == []

    def test_single_claim(self) -> None:
        answer = "The capital of France is Paris, a major European city."
        claims = extract_claims(answer)
        assert len(claims) >= 1

    def test_deduplication_not_needed_for_different_claims(self) -> None:
        answer = (
            "France has 68 million people. "
            "Germany has 83 million people. "
            "Italy has 59 million people."
        )
        claims = extract_claims(answer)
        assert len(claims) == 3
