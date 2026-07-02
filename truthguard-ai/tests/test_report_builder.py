"""Unit tests for the report_builder module."""

from app.schemas import (
    Citation,
    ClaimVerdict,
    EvidenceItem,
    RiskLevel,
    Verdict,
)
from app.core.report_builder import build_report


class TestBuildReport:
    """Tests for the build_report function."""

    def _make_verdicts(self, verdicts: list[Verdict]) -> list[ClaimVerdict]:
        """Helper to quickly create ClaimVerdict objects."""
        return [
            ClaimVerdict(
                claim_index=i,
                verdict=v,
                confidence=0.8,
                evidence_indices=[],
                reasoning="test",
            )
            for i, v in enumerate(verdicts)
        ]

    def test_all_supported_gives_low_risk(self) -> None:
        verdicts = self._make_verdicts([Verdict.SUPPORTED, Verdict.SUPPORTED])
        report = build_report(
            extracted_claims=["claim A", "claim B"],
            evidence_items=[],
            claim_verdicts=verdicts,
            citations=[],
        )
        assert report.hallucination_risk_score == 0.0
        assert report.risk_level == RiskLevel.LOW

    def test_all_contradicted_gives_high_risk(self) -> None:
        verdicts = self._make_verdicts([Verdict.CONTRADICTED, Verdict.CONTRADICTED])
        report = build_report(
            extracted_claims=["claim A", "claim B"],
            evidence_items=[],
            claim_verdicts=verdicts,
            citations=[],
        )
        assert report.hallucination_risk_score == 1.0
        assert report.risk_level == RiskLevel.HIGH

    def test_mixed_verdicts_gives_medium_risk(self) -> None:
        verdicts = self._make_verdicts([
            Verdict.SUPPORTED,
            Verdict.NOT_ENOUGH_EVIDENCE,
            Verdict.CONTRADICTED,
        ])
        report = build_report(
            extracted_claims=["claim A", "claim B", "claim C"],
            evidence_items=[],
            claim_verdicts=verdicts,
            citations=[],
        )
        # Score = (0.0 + 0.5 + 1.0) / 3 = 0.5
        assert report.hallucination_risk_score == 0.5
        assert report.risk_level == RiskLevel.MEDIUM

    def test_empty_verdicts_gives_zero_risk(self) -> None:
        report = build_report(
            extracted_claims=[],
            evidence_items=[],
            claim_verdicts=[],
            citations=[],
        )
        assert report.hallucination_risk_score == 0.0
        assert report.risk_level == RiskLevel.LOW

    def test_summary_contains_verdict_counts(self) -> None:
        verdicts = self._make_verdicts([
            Verdict.SUPPORTED,
            Verdict.CONTRADICTED,
            Verdict.NOT_ENOUGH_EVIDENCE,
        ])
        report = build_report(
            extracted_claims=["a", "b", "c"],
            evidence_items=[],
            claim_verdicts=verdicts,
            citations=[],
        )
        assert "1 of 3 claims are supported" in report.final_summary
        assert "1 claim contradict evidence" in report.final_summary
        assert "1 claim lack sufficient evidence" in report.final_summary

    def test_citations_passed_through(self) -> None:
        citations = [
            Citation(claim_index=0, source="wiki", url="https://example.com", confidence=0.9),
        ]
        report = build_report(
            extracted_claims=["claim"],
            evidence_items=[],
            claim_verdicts=self._make_verdicts([Verdict.SUPPORTED]),
            citations=citations,
        )
        assert len(report.citations) == 1
        assert report.citations[0].source == "wiki"
