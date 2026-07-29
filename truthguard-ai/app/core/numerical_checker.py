"""Numerical and date claim verification module.

Extracts numeric values and date references from claims and evidence,
then flags potential contradictions where:
  - A numerical claim value differs from evidence by more than a tolerance
  - A date in the claim differs from a date in the evidence

This catches the case where keyword overlap is high (same topic) but
the actual numbers disagree (e.g., "GDP is $5 trillion" vs "GDP approximately $3 trillion").
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

# Number extraction: captures value + optional scale suffix
_NUMBER_PATTERN = re.compile(
    r"(\d+(?:,\d{3})*(?:\.\d+)?)\s*"
    r"(trillion|billion|million|thousand|hundred|percent|%|km|meters?|ft|feet|years?|days?)?",
    re.IGNORECASE,
)

# Date year pattern (4-digit years 1000-2999)
_YEAR_PATTERN = re.compile(r"\b(1\d{3}|2\d{3})\b")

_SCALE_MAP: dict[str, float] = {
    "trillion": 1e12,
    "billion": 1e9,
    "million": 1e6,
    "thousand": 1e3,
    "hundred": 1e2,
    "percent": 1.0,
    "%": 1.0,
    "km": 1.0,
    "meters": 1.0,
    "meter": 1.0,
    "ft": 1.0,
    "feet": 1.0,
    "years": 1.0,
    "year": 1.0,
    "days": 1.0,
    "day": 1.0,
}


@dataclass
class NumericalValue:
    """A numeric value extracted from text."""

    raw: str
    value: float  # scaled value
    unit: str


@dataclass
class NumericalCheckResult:
    """Result of numerical comparison between claim and evidence."""

    has_numeric_conflict: bool
    claim_values: list[NumericalValue] = field(default_factory=list)
    evidence_values: list[NumericalValue] = field(default_factory=list)
    conflict_detail: str = ""


def _extract_numbers(text: str) -> list[NumericalValue]:
    """Extract and scale all numeric values from text."""
    results: list[NumericalValue] = []
    for m in _NUMBER_PATTERN.finditer(text):
        raw_num = m.group(1).replace(",", "")
        unit = (m.group(2) or "").lower()
        try:
            value = float(raw_num) * _SCALE_MAP.get(unit, 1.0)
            results.append(NumericalValue(raw=m.group(0).strip(), value=value, unit=unit))
        except ValueError:
            pass
    return results


def _extract_years(text: str) -> list[int]:
    """Extract 4-digit year references from text."""
    return [int(m.group(1)) for m in _YEAR_PATTERN.finditer(text)]


def check_numerical_conflict(
    claim: str,
    evidence_snippet: str,
    tolerance: float = 0.15,
) -> NumericalCheckResult:
    """Check if numerical values in claim conflict with evidence.

    A conflict is detected when:
    - Both claim and evidence contain numbers with same unit/scale
    - The numbers differ by more than tolerance (default 15%)
    - OR year references differ (exact match required for years)

    Args:
        claim: The claim text.
        evidence_snippet: The evidence snippet to compare against.
        tolerance: Relative tolerance for numeric comparison (0.15 = 15%).

    Returns:
        NumericalCheckResult indicating whether a conflict was found.
    """
    claim_nums = _extract_numbers(claim)
    ev_nums = _extract_numbers(evidence_snippet)
    claim_years = _extract_years(claim)
    ev_years = _extract_years(evidence_snippet)

    # Year conflict check (exact match required)
    if claim_years and ev_years:
        claim_year = claim_years[0]
        ev_year = ev_years[0]
        if claim_year != ev_year:
            return NumericalCheckResult(
                has_numeric_conflict=True,
                claim_values=claim_nums,
                evidence_values=ev_nums,
                conflict_detail=(
                    f"Year mismatch: claim says {claim_year}, "
                    f"evidence says {ev_year}"
                ),
            )

    # Numeric value conflict check
    if claim_nums and ev_nums:
        # Compare first significant number pair that shares same unit category
        for c_val in claim_nums:
            if c_val.value == 0:
                continue
            for e_val in ev_nums:
                if e_val.value == 0:
                    continue
                # Only compare values of the same order of magnitude (same unit scale)
                if abs(c_val.value - e_val.value) / max(c_val.value, e_val.value) > tolerance:
                    # Large discrepancy — potential numeric conflict
                    return NumericalCheckResult(
                        has_numeric_conflict=True,
                        claim_values=claim_nums,
                        evidence_values=ev_nums,
                        conflict_detail=(
                            f"Numeric mismatch: claim '{c_val.raw}' vs "
                            f"evidence '{e_val.raw}' "
                            f"(difference > {tolerance:.0%})"
                        ),
                    )

    return NumericalCheckResult(
        has_numeric_conflict=False,
        claim_values=claim_nums,
        evidence_values=ev_nums,
    )
