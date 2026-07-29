"""TruthGuard-AI HTTP adapter for TruthBench.

Connects TruthBench's evaluation harness to a live TruthGuard-AI
service so the benchmark evaluates the real pipeline rather than
mock predictions.

Usage::

    from truthbench.adapters.truthguard_adapter import TruthGuardAdapter

    adapter = TruthGuardAdapter(base_url="http://127.0.0.1:8000")
    predicted = adapter.predict(eval_case)
    # predicted is a PredictedResult matching TruthBench schemas

Environment variables:
    TRUTHGUARD_BASE_URL   URL of the running TruthGuard-AI instance
                          (default: http://127.0.0.1:8000)
    TRUTHGUARD_API_KEY    API key if the service requires authentication
                          (default: empty — dev mode)
"""

from __future__ import annotations

import logging
import os
from typing import Any

from truthbench.schemas import (  # noqa: E402 (relative import from parent)
    EvaluationCase,
    PredictedClaim,
    PredictedResult,
    PredictedVerdict,
    RiskLevel,
    Verdict,
)

logger = logging.getLogger(__name__)

_DEFAULT_URL = "http://127.0.0.1:8000"
_VERDICT_MAP: dict[str, Verdict] = {
    "SUPPORTED": Verdict.SUPPORTED,
    "CONTRADICTED": Verdict.CONTRADICTED,
    "NOT_ENOUGH_EVIDENCE": Verdict.NOT_ENOUGH_EVIDENCE,
}
_RISK_MAP: dict[str, RiskLevel] = {
    "LOW": RiskLevel.LOW,
    "MEDIUM": RiskLevel.MEDIUM,
    "HIGH": RiskLevel.HIGH,
}


class TruthGuardAdapter:
    """Calls the live TruthGuard-AI /verify endpoint and adapts the response
    into TruthBench's PredictedResult schema.

    Args:
        base_url: Base URL of the TruthGuard-AI service.
        api_key:  Optional API key for authenticated deployments.
        timeout:  HTTP request timeout in seconds (default 30).
    """

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: int = 30,
    ) -> None:
        self.base_url = (base_url or os.environ.get("TRUTHGUARD_BASE_URL", _DEFAULT_URL)).rstrip("/")
        self.api_key = api_key or os.environ.get("TRUTHGUARD_API_KEY", "")
        self.timeout = timeout

    def _build_headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers

    def predict(self, case: EvaluationCase) -> PredictedResult:
        """Call TruthGuard-AI for a single evaluation case.

        Args:
            case: An EvaluationCase from the TruthBench dataset.

        Returns:
            PredictedResult populated from the TruthGuard-AI response.

        Raises:
            RuntimeError: If the HTTP call fails or the response is unexpected.
        """
        try:
            import urllib.request
            import urllib.error
            import json

            payload = json.dumps({
                "original_question": case.original_question,
                "generated_answer": case.generated_answer,
                # trusted_reference_evidence contains source names in TruthBench
                "trusted_sources": list(case.trusted_reference_evidence) or None,
            }).encode()

            req = urllib.request.Request(
                url=f"{self.base_url}/verify",
                data=payload,
                headers=self._build_headers(),
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data: dict[str, Any] = json.loads(resp.read())

        except Exception as exc:
            raise RuntimeError(
                f"TruthGuardAdapter: HTTP call to {self.base_url}/verify failed: {exc}"
            ) from exc

        # Map response to PredictedResult
        raw_verdicts: list[dict] = data.get("claim_verdicts", [])
        claims: list[str] = data.get("extracted_claims", [])

        # Build PredictedClaim list
        extracted_claims: list[PredictedClaim] = [
            PredictedClaim(text=c, claim_type="factual") for c in claims
        ]

        # Build PredictedVerdict list
        predicted_verdicts: list[PredictedVerdict] = []
        for v in raw_verdicts:
            idx = v.get("claim_index", 0)
            claim_text = claims[idx] if idx < len(claims) else f"Claim {idx}"
            raw_v = v.get("verdict", "NOT_ENOUGH_EVIDENCE")
            predicted_verdicts.append(
                PredictedVerdict(
                    claim_text=claim_text,
                    verdict=_VERDICT_MAP.get(raw_v, Verdict.NOT_ENOUGH_EVIDENCE),
                    confidence=v.get("confidence", 0.0),
                    reasoning=v.get("reasoning", ""),
                )
            )

        raw_risk = data.get("risk_level", "HIGH")
        risk_level = _RISK_MAP.get(raw_risk, RiskLevel.HIGH)
        risk_score: float = data.get("hallucination_risk_score", 1.0)
        citations: list[str] = [
            c.get("url") or c.get("source", "") for c in data.get("citations", [])
        ]

        logger.debug(
            "TruthGuardAdapter: question=%r, risk=%s (%.2f), %d verdicts",
            case.original_question[:60], raw_risk, risk_score, len(predicted_verdicts),
        )

        return PredictedResult(
            case_id=case.id,
            extracted_claims=extracted_claims,
            predicted_verdicts=predicted_verdicts,
            hallucination_risk_score=risk_score,
            risk_level=risk_level,
            citations=citations,
        )
