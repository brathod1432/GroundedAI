"""TruthGuard-AI client — calls the ``/verify`` endpoint of truthguard-ai.

Includes a real HTTP client and a mock for local development and testing.
"""

from __future__ import annotations

import logging
import re
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


# ── Real client ──────────────────────────────────────────────────────────


class TruthGuardClient:
    """HTTP client that calls the live TruthGuard-AI ``/verify`` endpoint."""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def verify(
        self,
        question: str,
        answer: str,
        trusted_sources: list[str] | None = None,
    ) -> dict[str, Any]:
        """Call TruthGuard ``/verify`` and return the JSON response dict.

        Raises
        ------
        httpx.HTTPStatusError
            If the upstream service returns a non-2xx status.
        """
        payload: dict[str, Any] = {
            "original_question": question,
            "generated_answer": answer,
        }
        if trusted_sources is not None:
            payload["trusted_sources"] = trusted_sources

        url = f"{self.base_url}/verify"
        logger.info("Calling TruthGuard at %s", url)

        with httpx.Client(timeout=60.0) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            return response.json()


# ── Mock client ──────────────────────────────────────────────────────────


class MockTruthGuardClient:
    """Simulates TruthGuard verification without needing the real service.

    Behaviour:
    - **First call** → returns ``HIGH`` risk with contradicted claims.
    - **Subsequent calls** → returns ``LOW`` risk (simulating successful
      correction).
    """

    def __init__(self) -> None:
        self._call_count: int = 0

    def verify(
        self,
        question: str,
        answer: str,
        trusted_sources: list[str] | None = None,
    ) -> dict[str, Any]:
        """Return a mock verification response."""
        self._call_count += 1

        # Split answer into simple sentence-level claims.
        claims = [
            s.strip()
            for s in re.split(r"[.!?]+", answer)
            if s.strip() and len(s.strip()) > 5
        ]
        if not claims:
            claims = [answer[:200]]

        if self._call_count == 1:
            # First iteration: HIGH risk — some contradicted claims.
            contradicted = claims[: max(1, len(claims) // 2)]
            supported = claims[max(1, len(claims) // 2) :]

            verdicts = []
            evidence_items = []
            for idx, claim in enumerate(claims):
                if claim in contradicted:
                    verdicts.append(
                        {
                            "claim_index": idx,
                            "verdict": "CONTRADICTED",
                            "confidence": 0.85,
                            "evidence_indices": [idx],
                            "reasoning": f"Claim contradicts trusted evidence.",
                        }
                    )
                else:
                    verdicts.append(
                        {
                            "claim_index": idx,
                            "verdict": "SUPPORTED",
                            "confidence": 0.90,
                            "evidence_indices": [idx],
                            "reasoning": "Claim is supported by evidence.",
                        }
                    )
                evidence_items.append(
                    {
                        "claim_index": idx,
                        "source": "mock-source",
                        "snippet": f"Trusted evidence for claim {idx}: factual information.",
                        "url": "https://example.com/evidence",
                        "relevance_score": 0.9,
                    }
                )

            return {
                "extracted_claims": claims,
                "evidence_items": evidence_items,
                "claim_verdicts": verdicts,
                "hallucination_risk_score": 0.75,
                "risk_level": "HIGH",
                "final_summary": (
                    f"Verification found {len(contradicted)} contradicted claim(s) "
                    f"and {len(supported)} supported claim(s). Risk is HIGH."
                ),
                "citations": [],
            }

        # Subsequent iterations: LOW risk — everything supported.
        verdicts = [
            {
                "claim_index": idx,
                "verdict": "SUPPORTED",
                "confidence": 0.95,
                "evidence_indices": [idx],
                "reasoning": "Claim is well-supported by evidence.",
            }
            for idx, _claim in enumerate(claims)
        ]
        evidence_items = [
            {
                "claim_index": idx,
                "source": "mock-source",
                "snippet": f"Trusted evidence for claim {idx}: factual information.",
                "url": "https://example.com/evidence",
                "relevance_score": 0.95,
            }
            for idx, _claim in enumerate(claims)
        ]

        return {
            "extracted_claims": claims,
            "evidence_items": evidence_items,
            "claim_verdicts": verdicts,
            "hallucination_risk_score": 0.10,
            "risk_level": "LOW",
            "final_summary": (
                f"All {len(claims)} claims are supported by trusted evidence. "
                "Risk is LOW."
            ),
            "citations": [],
        }


# ── Factory ──────────────────────────────────────────────────────────────


def get_truthguard_client() -> TruthGuardClient | MockTruthGuardClient:
    """Return a TruthGuard client based on the current configuration.

    When ``settings.llm_provider`` is ``"mock"`` the mock client is
    returned so the pipeline works without a running TruthGuard service.
    """
    if settings.llm_provider == "mock":
        logger.info("Using MockTruthGuardClient (llm_provider=mock)")
        return MockTruthGuardClient()

    logger.info(
        "Using TruthGuardClient pointing to %s", settings.truthguard_url
    )
    return TruthGuardClient(base_url=settings.truthguard_url)
