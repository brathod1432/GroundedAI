"""Unit tests for the verifier module."""

from app.schemas import ClaimVerdict, EvidenceItem, Verdict
from app.core.verifier import verify_claims


class TestVerifyClaims:
    """Tests for the verify_claims function."""

    def test_no_evidence_gives_not_enough_evidence(self) -> None:
        claims = ["The population of France is 68 million."]
        verdicts = verify_claims(claims, evidence_items=[])
        assert len(verdicts) == 1
        assert verdicts[0].verdict == Verdict.NOT_ENOUGH_EVIDENCE

    def test_supporting_evidence_gives_supported(self) -> None:
        claims = ["France population million estimated."]
        evidence = [
            EvidenceItem(
                claim_index=0,
                source="wikipedia",
                snippet="France's population was estimated at 68 million in 2023.",
                url="https://en.wikipedia.org/wiki/France",
                relevance_score=0.90,
            )
        ]
        verdicts = verify_claims(claims, evidence)
        assert len(verdicts) == 1
        assert verdicts[0].verdict == Verdict.SUPPORTED

    def test_contradicted_evidence(self) -> None:
        claims = ["France population million estimated."]
        evidence = [
            EvidenceItem(
                claim_index=0,
                source="fact-check",
                snippet="It is false and incorrect that France has 100 million people.",
                url="https://example.com/factcheck",
                relevance_score=0.85,
            )
        ]
        verdicts = verify_claims(claims, evidence)
        assert len(verdicts) == 1
        assert verdicts[0].verdict == Verdict.CONTRADICTED

    def test_multiple_claims(self) -> None:
        claims = [
            "France population million estimated.",
            "Paris is a small village in Germany.",
        ]
        evidence = [
            EvidenceItem(
                claim_index=0,
                source="wikipedia",
                snippet="France's population was estimated at 68 million.",
                url="",
                relevance_score=0.90,
            ),
        ]
        verdicts = verify_claims(claims, evidence)
        assert len(verdicts) == 2
        # First claim has evidence (should be SUPPORTED)
        assert verdicts[0].verdict == Verdict.SUPPORTED
        # Second claim has no evidence → NOT_ENOUGH_EVIDENCE
        assert verdicts[1].verdict == Verdict.NOT_ENOUGH_EVIDENCE

    def test_empty_claims_list(self) -> None:
        verdicts = verify_claims([], evidence_items=[])
        assert verdicts == []

    def test_out_of_range_evidence_is_ignored(self) -> None:
        """Evidence referencing a non-existent claim index should not crash."""
        claims = ["France has 68 million people."]
        evidence = [
            EvidenceItem(
                claim_index=99,  # out of range
                source="wikipedia",
                snippet="Some unrelated text.",
                url="",
                relevance_score=0.5,
            )
        ]
        verdicts = verify_claims(claims, evidence)
        assert len(verdicts) == 1
        # Claim 0 has no matching evidence
        assert verdicts[0].verdict == Verdict.NOT_ENOUGH_EVIDENCE
