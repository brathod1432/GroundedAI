"""Tests for the text processing utilities module."""

from app.utils.text_utils import extract_keywords, normalize_whitespace, split_into_sentences


# ── split_into_sentences ─────────────────────────────────────────────────

class TestSplitIntoSentences:
    """Tests for split_into_sentences."""

    def test_single_sentence(self):
        """A single sentence should return a one-element list."""
        result = split_into_sentences("Paris is the capital of France.")
        assert result == ["Paris is the capital of France."]

    def test_multiple_sentences(self):
        """Multiple sentences separated by periods should be split correctly."""
        text = "Paris is the capital. It is in Europe. The Eiffel Tower is there."
        result = split_into_sentences(text)
        assert len(result) == 3
        assert result[0] == "Paris is the capital."
        assert result[1] == "It is in Europe."
        assert result[2] == "The Eiffel Tower is there."

    def test_empty_input(self):
        """An empty string should return an empty list."""
        result = split_into_sentences("")
        assert result == []

    def test_question_marks(self):
        """Sentences ending with question marks should be split."""
        text = "What is the capital? It is Paris."
        result = split_into_sentences(text)
        assert len(result) == 2

    def test_exclamation_marks(self):
        """Sentences ending with exclamation marks should be split."""
        text = "What a city! Paris is amazing."
        result = split_into_sentences(text)
        assert len(result) == 2

    def test_whitespace_only(self):
        """Whitespace-only input should return an empty list."""
        result = split_into_sentences("   ")
        assert result == []


# ── normalize_whitespace ─────────────────────────────────────────────────

class TestNormalizeWhitespace:
    """Tests for normalize_whitespace."""

    def test_multiple_spaces(self):
        """Multiple spaces should collapse into a single space."""
        assert normalize_whitespace("hello   world") == "hello world"

    def test_tabs_and_newlines(self):
        """Tabs and newlines should be replaced with a single space."""
        assert normalize_whitespace("hello\t\tworld\n\nfoo") == "hello world foo"

    def test_leading_trailing_whitespace(self):
        """Leading and trailing whitespace should be stripped."""
        assert normalize_whitespace("  hello world  ") == "hello world"

    def test_mixed_whitespace(self):
        """Mixed whitespace types should all collapse properly."""
        assert normalize_whitespace("a \t b \n c") == "a b c"

    def test_single_space(self):
        """Already-clean text should remain unchanged."""
        assert normalize_whitespace("hello world") == "hello world"


# ── extract_keywords ─────────────────────────────────────────────────────

class TestExtractKeywords:
    """Tests for extract_keywords."""

    def test_filters_short_words(self):
        """Words shorter than min_length (default 4) should be excluded."""
        result = extract_keywords("I am a dog but also big")
        # "I", "am", "a", "dog", "but", "big" are all < 4 chars
        # "also" is exactly 4 chars and is a stopword? No, "also" is in the stop_words set.
        assert "dog" not in result  # len("dog") == 3
        assert "big" not in result  # len("big") == 3
        assert "am" not in result   # len("am") == 2

    def test_returns_lowercase(self):
        """All returned keywords should be lowercase."""
        result = extract_keywords("Paris France Europe Capital")
        for keyword in result:
            assert keyword == keyword.lower()
        assert "paris" in result
        assert "france" in result

    def test_removes_stopwords(self):
        """Common stopwords should be filtered out."""
        result = extract_keywords("This is about which other things would happen")
        # "this", "about", "which", "other", "would" are stopwords
        assert "this" not in result
        assert "about" not in result
        assert "which" not in result
        assert "other" not in result
        assert "would" not in result

    def test_deduplication(self):
        """Repeated words should only appear once in the result."""
        result = extract_keywords("Paris Paris Paris capital capital")
        assert result.count("paris") == 1
        assert result.count("capital") == 1

    def test_custom_min_length(self):
        """Custom min_length should override the default."""
        result = extract_keywords("big dog cat elephant", min_length=3)
        assert "big" in result
        assert "dog" in result
        assert "cat" in result
        assert "elephant" in result

    def test_empty_input(self):
        """Empty input should return an empty list."""
        result = extract_keywords("")
        assert result == []

    def test_extracts_content_words(self):
        """Should extract meaningful content words from a real sentence."""
        result = extract_keywords("The population of France is approximately sixty million")
        assert "population" in result
        assert "france" in result
        assert "approximately" in result
