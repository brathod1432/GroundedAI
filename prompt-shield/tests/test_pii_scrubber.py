"""Tests for the PII scrubbing and restoration engine."""
from __future__ import annotations

import pytest

from app.core.pii_scrubber import ScrubResult, scrub_pii, restore_pii


class TestScrubPII:
    """Tests for scrub_pii()."""

    def test_single_email_replaced_with_placeholder(self):
        result = scrub_pii("Contact john@example.com please")
        assert isinstance(result, ScrubResult)
        assert "[EMAIL_1]" in result.sanitized_text
        assert "john@example.com" not in result.sanitized_text

    def test_multiple_pii_get_unique_placeholders(self):
        result = scrub_pii("Email john@a.com and call 555-123-4567")
        assert "[EMAIL_1]" in result.sanitized_text
        assert "[PHONE_1]" in result.sanitized_text
        assert "john@a.com" not in result.sanitized_text
        assert "555-123-4567" not in result.sanitized_text

    def test_no_pii_returns_original_text(self):
        original = "The weather is nice today"
        result = scrub_pii(original)
        assert result.sanitized_text == original
        assert result.pii_mapping == {}
        assert result.matches == []

    def test_mapping_contains_placeholder_to_original(self):
        result = scrub_pii("My email is john@example.com")
        assert "[EMAIL_1]" in result.pii_mapping
        assert result.pii_mapping["[EMAIL_1]"] == "john@example.com"

    def test_multiple_same_type_get_sequential_numbers(self):
        result = scrub_pii("a@b.com and c@d.com")
        assert "[EMAIL_1]" in result.sanitized_text
        assert "[EMAIL_2]" in result.sanitized_text
        assert "[EMAIL_1]" in result.pii_mapping
        assert "[EMAIL_2]" in result.pii_mapping

    def test_empty_string_returns_empty(self):
        result = scrub_pii("")
        assert result.sanitized_text == ""
        assert result.pii_mapping == {}
        assert result.matches == []

    def test_non_pii_text_preserved_around_placeholders(self):
        result = scrub_pii("Hello john@example.com world")
        # The text around the placeholder should remain intact
        assert result.sanitized_text.startswith("Hello ")
        assert result.sanitized_text.endswith(" world")

    def test_scrub_result_has_matches(self):
        result = scrub_pii("test john@example.com done")
        assert len(result.matches) == 1
        assert result.matches[0].pii_type == "email"
        assert result.matches[0].value == "john@example.com"


class TestRestorePII:
    """Tests for restore_pii()."""

    def test_restore_single_placeholder(self):
        mapping = {"[EMAIL_1]": "john@example.com"}
        result = restore_pii("Contact [EMAIL_1] please", mapping)
        assert result == "Contact john@example.com please"

    def test_restore_multiple_placeholders(self):
        mapping = {
            "[EMAIL_1]": "john@example.com",
            "[PHONE_1]": "555-123-4567",
        }
        text = "Email [EMAIL_1] or call [PHONE_1]"
        result = restore_pii(text, mapping)
        assert "john@example.com" in result
        assert "555-123-4567" in result
        assert "[EMAIL_1]" not in result
        assert "[PHONE_1]" not in result

    def test_empty_mapping_returns_text_unchanged(self):
        text = "No placeholders here"
        result = restore_pii(text, {})
        assert result == text

    def test_round_trip_scrub_then_restore(self):
        original = "Email john@example.com and call 555-123-4567 ok"
        scrub_result = scrub_pii(original)
        restored = restore_pii(scrub_result.sanitized_text, scrub_result.pii_mapping)
        assert restored == original

    def test_round_trip_no_pii(self):
        original = "Just a clean sentence"
        scrub_result = scrub_pii(original)
        restored = restore_pii(scrub_result.sanitized_text, scrub_result.pii_mapping)
        assert restored == original

    def test_round_trip_multiple_same_type(self):
        original = "a@b.com and c@d.com"
        scrub_result = scrub_pii(original)
        restored = restore_pii(scrub_result.sanitized_text, scrub_result.pii_mapping)
        assert restored == original
