"""Tests for the PII detection engine."""
from __future__ import annotations

import pytest

from app.core.pii_detector import PIIMatch, detect_pii


class TestDetectPII:
    """Tests for detect_pii()."""

    # ── Email detection ──────────────────────────────────────────────

    def test_detects_single_email(self):
        matches = detect_pii("Contact me at john@example.com")
        assert len(matches) == 1
        assert matches[0].pii_type == "email"
        assert matches[0].value == "john@example.com"

    def test_detects_multiple_emails(self):
        matches = detect_pii("john@a.com and jane@b.com")
        emails = [m for m in matches if m.pii_type == "email"]
        assert len(emails) == 2
        values = {m.value for m in emails}
        assert "john@a.com" in values
        assert "jane@b.com" in values

    # ── Phone number detection ───────────────────────────────────────

    def test_detects_phone_number(self):
        matches = detect_pii("Call 555-123-4567")
        phones = [m for m in matches if m.pii_type == "phone"]
        assert len(phones) == 1
        assert "555-123-4567" in phones[0].value

    def test_detects_phone_with_country_code(self):
        matches = detect_pii("Call +1 (555) 123-4567")
        phones = [m for m in matches if m.pii_type == "phone"]
        assert len(phones) == 1
        assert "123-4567" in phones[0].value

    # ── SSN detection ────────────────────────────────────────────────

    def test_detects_ssn(self):
        matches = detect_pii("My SSN is 123-45-6789")
        ssns = [m for m in matches if m.pii_type == "ssn"]
        assert len(ssns) == 1
        assert ssns[0].value == "123-45-6789"

    # ── Credit card detection ────────────────────────────────────────

    def test_detects_credit_card(self):
        matches = detect_pii("Card: 4111-1111-1111-1111")
        cards = [m for m in matches if m.pii_type == "credit_card"]
        assert len(cards) == 1
        assert cards[0].value == "4111-1111-1111-1111"

    # ── API key detection ────────────────────────────────────────────

    def test_detects_api_key(self):
        matches = detect_pii(
            "Token: sk-abc123def456ghi789jkl012mno345pqr678"
        )
        keys = [m for m in matches if m.pii_type == "api_key"]
        assert len(keys) == 1
        assert keys[0].value.startswith("sk-")

    # ── IP address detection ─────────────────────────────────────────

    def test_detects_ip_address(self):
        matches = detect_pii("Server at 192.168.1.1")
        ips = [m for m in matches if m.pii_type == "ip_address"]
        assert len(ips) == 1
        assert ips[0].value == "192.168.1.1"

    # ── No PII / empty ───────────────────────────────────────────────

    def test_no_pii_returns_empty(self):
        matches = detect_pii("The weather is nice today")
        assert matches == []

    def test_empty_string_returns_empty(self):
        matches = detect_pii("")
        assert matches == []

    # ── Multiple PII types ───────────────────────────────────────────

    def test_multiple_pii_types(self):
        text = "Email john@example.com, call 555-123-4567"
        matches = detect_pii(text)
        types = {m.pii_type for m in matches}
        assert "email" in types
        assert "phone" in types
        assert len(matches) >= 2

    # ── Match structure ──────────────────────────────────────────────

    def test_match_has_correct_positions(self):
        text = "hi john@example.com bye"
        matches = detect_pii(text)
        assert len(matches) == 1
        m = matches[0]
        assert text[m.start : m.end] == "john@example.com"

    def test_matches_sorted_by_start_position(self):
        text = "a@b.com then 192.168.0.1 then c@d.com"
        matches = detect_pii(text)
        starts = [m.start for m in matches]
        assert starts == sorted(starts)

    def test_pii_match_dataclass_fields(self):
        matches = detect_pii("john@example.com")
        m = matches[0]
        assert isinstance(m, PIIMatch)
        assert hasattr(m, "pii_type")
        assert hasattr(m, "value")
        assert hasattr(m, "start")
        assert hasattr(m, "end")
