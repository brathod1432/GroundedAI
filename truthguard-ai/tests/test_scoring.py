"""Tests for the hallucination risk scoring module."""

import pytest

from app.schemas import ClaimVerdict, RiskLevel, Verdict
from app.services.scoring import compute_risk_score, compute_summary, score_to_risk_level


# ── Helpers ──────────────────────────────────────────────────────────────

def _make_verdict(verdict: Verdict, index: int = 0) -> ClaimVerdict:
    """Create a minimal ClaimVerdict for testing."""
    return ClaimVerdict(claim_index=index, verdict=verdict)


# ── compute_risk_score ───────────────────────────────────────────────────

class TestComputeRiskScore:
    """Tests for compute_risk_score."""

    def test_all_supported_returns_zero(self):
        """All SUPPORTED verdicts should yield a risk score of 0.0."""
        verdicts = [_make_verdict(Verdict.SUPPORTED, i) for i in range(5)]
        assert compute_risk_score(verdicts) == 0.0

    def test_all_contradicted_returns_one(self):
        """All CONTRADICTED verdicts should yield a risk score of 1.0."""
        verdicts = [_make_verdict(Verdict.CONTRADICTED, i) for i in range(5)]
        assert compute_risk_score(verdicts) == 1.0

    def test_mixed_verdicts(self):
        """A mix of verdicts should return a score between 0 and 1."""
        verdicts = [
            _make_verdict(Verdict.SUPPORTED, 0),
            _make_verdict(Verdict.CONTRADICTED, 1),
            _make_verdict(Verdict.NOT_ENOUGH_EVIDENCE, 2),
        ]
        score = compute_risk_score(verdicts)
        # Expected: (0.0 + 1.0 + 0.5) / 3 = 0.5
        assert score == pytest.approx(0.5)

    def test_empty_list_returns_zero(self):
        """An empty verdict list should return 0.0 (nothing suspicious)."""
        assert compute_risk_score([]) == 0.0

    def test_single_not_enough_evidence(self):
        """A single NOT_ENOUGH_EVIDENCE verdict should return 0.5."""
        verdicts = [_make_verdict(Verdict.NOT_ENOUGH_EVIDENCE)]
        assert compute_risk_score(verdicts) == pytest.approx(0.5)

    def test_score_never_exceeds_one(self):
        """Score should be capped at 1.0 regardless of input."""
        verdicts = [_make_verdict(Verdict.CONTRADICTED, i) for i in range(100)]
        assert compute_risk_score(verdicts) <= 1.0


# ── score_to_risk_level ──────────────────────────────────────────────────

class TestScoreToRiskLevel:
    """Tests for score_to_risk_level."""

    def test_low_threshold(self):
        """Scores <= 0.33 should map to LOW."""
        assert score_to_risk_level(0.0) == RiskLevel.LOW
        assert score_to_risk_level(0.1) == RiskLevel.LOW
        assert score_to_risk_level(0.33) == RiskLevel.LOW

    def test_medium_threshold(self):
        """Scores in (0.33, 0.66] should map to MEDIUM."""
        assert score_to_risk_level(0.34) == RiskLevel.MEDIUM
        assert score_to_risk_level(0.5) == RiskLevel.MEDIUM
        assert score_to_risk_level(0.66) == RiskLevel.MEDIUM

    def test_high_threshold(self):
        """Scores > 0.66 should map to HIGH."""
        assert score_to_risk_level(0.67) == RiskLevel.HIGH
        assert score_to_risk_level(0.9) == RiskLevel.HIGH
        assert score_to_risk_level(1.0) == RiskLevel.HIGH


# ── compute_summary ──────────────────────────────────────────────────────

class TestComputeSummary:
    """Tests for compute_summary."""

    def test_all_supported_summary(self):
        """Summary should mention supported claims and LOW risk."""
        verdicts = [_make_verdict(Verdict.SUPPORTED, i) for i in range(3)]
        summary = compute_summary(verdicts, 0.0, RiskLevel.LOW)
        assert "3 of 3 claims are supported" in summary
        assert "LOW" in summary
        assert "0.00" in summary

    def test_all_contradicted_summary(self):
        """Summary should mention contradicted claims and HIGH risk."""
        verdicts = [_make_verdict(Verdict.CONTRADICTED, i) for i in range(2)]
        summary = compute_summary(verdicts, 1.0, RiskLevel.HIGH)
        assert "2 claims contradict evidence" in summary
        assert "HIGH" in summary

    def test_single_contradicted_singular(self):
        """A single contradicted claim should use singular form."""
        verdicts = [_make_verdict(Verdict.CONTRADICTED, 0)]
        summary = compute_summary(verdicts, 1.0, RiskLevel.HIGH)
        assert "1 claim contradict evidence" in summary

    def test_mixed_summary(self):
        """Summary should mention all verdict categories when mixed."""
        verdicts = [
            _make_verdict(Verdict.SUPPORTED, 0),
            _make_verdict(Verdict.CONTRADICTED, 1),
            _make_verdict(Verdict.NOT_ENOUGH_EVIDENCE, 2),
        ]
        summary = compute_summary(verdicts, 0.5, RiskLevel.MEDIUM)
        assert "1 of 3 claims are supported" in summary
        assert "1 claim contradict evidence" in summary
        assert "1 claim lack sufficient evidence" in summary
        assert "MEDIUM" in summary

    def test_summary_includes_score(self):
        """Summary should always include the numeric risk score."""
        verdicts = [_make_verdict(Verdict.SUPPORTED, 0)]
        summary = compute_summary(verdicts, 0.15, RiskLevel.LOW)
        assert "0.15" in summary

    def test_not_enough_evidence_plural(self):
        """Multiple NOT_ENOUGH_EVIDENCE claims should use plural form."""
        verdicts = [_make_verdict(Verdict.NOT_ENOUGH_EVIDENCE, i) for i in range(3)]
        summary = compute_summary(verdicts, 0.5, RiskLevel.MEDIUM)
        assert "3 claims lack sufficient evidence" in summary
