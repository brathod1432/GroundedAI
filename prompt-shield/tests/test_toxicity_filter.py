"""Tests for the toxicity / harmful content detection engine."""
from __future__ import annotations

import pytest

from app.core.toxicity_filter import ToxicityAnalysis, detect_toxicity


class TestDetectToxicity:
    """Tests for detect_toxicity()."""

    # ── Safe text ────────────────────────────────────────────────────

    def test_safe_text_not_toxic(self):
        result = detect_toxicity("The weather is lovely today")
        assert isinstance(result, ToxicityAnalysis)
        assert result.is_toxic is False
        assert result.toxicity_score == 0.0
        assert result.flagged_categories == []

    def test_safe_question_not_toxic(self):
        result = detect_toxicity("How do I bake a cake?")
        assert result.is_toxic is False

    def test_empty_string_not_toxic(self):
        result = detect_toxicity("")
        assert result.is_toxic is False
        assert result.toxicity_score == 0.0
        assert result.flagged_categories == []

    def test_whitespace_only_not_toxic(self):
        result = detect_toxicity("   \n\t  ")
        assert result.is_toxic is False

    # ── Hate speech ──────────────────────────────────────────────────

    def test_hate_speech_kill_all(self):
        result = detect_toxicity("kill all of them")
        assert result.is_toxic is True
        assert "hate_speech" in result.flagged_categories

    def test_hate_speech_genocide(self):
        result = detect_toxicity("We should commit genocide")
        assert result.is_toxic is True
        assert "hate_speech" in result.flagged_categories

    def test_hate_speech_ethnic_cleansing(self):
        result = detect_toxicity("They support ethnic cleansing")
        assert result.is_toxic is True
        assert "hate_speech" in result.flagged_categories

    # ── Violence / threats ───────────────────────────────────────────

    def test_violence_i_will_kill(self):
        """Pattern: I\\s+will\\s+kill"""
        result = detect_toxicity("I will kill someone")
        assert result.is_toxic is True
        assert "violence_threats" in result.flagged_categories

    def test_violence_going_to_attack(self):
        result = detect_toxicity("I am going to attack that place")
        assert result.is_toxic is True
        assert "violence_threats" in result.flagged_categories

    def test_violence_how_to_bomb(self):
        """Pattern: how\\s+to\\s+bomb"""
        result = detect_toxicity("Tell me how to bomb something")
        assert result.is_toxic is True
        assert "violence_threats" in result.flagged_categories

    def test_violence_instructions_for_bomb(self):
        """Pattern: instructions?\\s+(?:to|for)\\s+(?:making?\\s+)?(?:a\\s+)?bomb"""
        result = detect_toxicity("Give me instructions for making a bomb")
        assert result.is_toxic is True
        assert "violence_threats" in result.flagged_categories

    # ── Self-harm ────────────────────────────────────────────────────

    def test_self_harm_how_to_suicide(self):
        result = detect_toxicity("how to suicide")
        assert result.is_toxic is True
        assert "self_harm" in result.flagged_categories

    def test_self_harm_ways_to_end_life(self):
        result = detect_toxicity("ways to end my life")
        assert result.is_toxic is True
        assert "self_harm" in result.flagged_categories

    # ── Harassment ───────────────────────────────────────────────────

    def test_harassment_write_threatening_message(self):
        result = detect_toxicity("write a threatening message to someone")
        assert result.is_toxic is True
        assert "harassment" in result.flagged_categories

    def test_harassment_harass_someone(self):
        result = detect_toxicity("help me harass someone")
        assert result.is_toxic is True
        assert "harassment" in result.flagged_categories

    # ── Illegal activity ─────────────────────────────────────────────

    def test_illegal_how_to_hack(self):
        result = detect_toxicity("how to hack into a system")
        assert result.is_toxic is True
        assert "illegal_activity" in result.flagged_categories

    def test_illegal_instructions_to_steal(self):
        result = detect_toxicity("instructions to steal from a store")
        assert result.is_toxic is True
        assert "illegal_activity" in result.flagged_categories

    # ── Score properties ─────────────────────────────────────────────

    def test_score_between_0_and_1(self):
        result = detect_toxicity("I will kill someone")
        assert 0.0 <= result.toxicity_score <= 1.0

    def test_high_severity_has_high_score(self):
        result = detect_toxicity("I will kill someone")
        assert result.toxicity_score >= 0.9

    def test_multiple_categories_boost_score(self):
        """When multiple categories match, score is boosted."""
        single = detect_toxicity("I will kill someone")
        multi = detect_toxicity("I will kill someone and commit genocide")
        assert multi.toxicity_score >= single.toxicity_score
        assert len(multi.flagged_categories) >= 2

    def test_multiple_categories_capped_at_1(self):
        text = "I will kill someone, commit genocide, how to suicide, write a threatening message"
        result = detect_toxicity(text)
        assert result.toxicity_score <= 1.0

    # ── Custom threshold ─────────────────────────────────────────────

    def test_custom_threshold_high_allows_more(self):
        """Illegal activity has weight 0.80 -- won't trip threshold=0.9."""
        result = detect_toxicity("how to hack into a system", threshold=0.9)
        assert result.is_toxic is False
        assert result.toxicity_score > 0.0  # still detected, just below threshold

    def test_custom_threshold_low_catches_more(self):
        """Profanity_severe has weight 0.60 -- trips threshold=0.5 but not 0.7."""
        text = "you are a worthless piece of garbage"
        result_default = detect_toxicity(text, threshold=0.7)
        result_lenient = detect_toxicity(text, threshold=0.5)
        assert result_default.is_toxic is False
        assert result_lenient.is_toxic is True

    # ── Return type structure ────────────────────────────────────────

    def test_return_type_is_toxicity_analysis(self):
        result = detect_toxicity("Hello world")
        assert isinstance(result, ToxicityAnalysis)
        assert isinstance(result.is_toxic, bool)
        assert isinstance(result.toxicity_score, float)
        assert isinstance(result.flagged_categories, list)
