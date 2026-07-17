"""Corrective prompt builder for the auto-grounding loop.

Constructs a structured prompt that instructs an LLM to rewrite a
hallucinated answer using *only* trusted evidence.
"""

from __future__ import annotations


def build_corrective_prompt(
    question: str,
    failed_answer: str,
    evidence: list[dict],
    contradicted_claims: list[str],
    unsupported_claims: list[str],
) -> str:
    """Build a corrective prompt for the LLM.

    Parameters
    ----------
    question:
        The original user question.
    failed_answer:
        The answer that failed verification.
    evidence:
        List of evidence dicts (each should contain at minimum a
        ``"snippet"`` key, and optionally ``"source"`` / ``"url"``).
    contradicted_claims:
        Claims from the answer that were contradicted by evidence.
    unsupported_claims:
        Claims from the answer that lacked sufficient evidence.

    Returns
    -------
    str
        A fully-formed corrective prompt ready for LLM completion.
    """

    sections: list[str] = []

    # ── Header ───────────────────────────────────────────────────────
    sections.append(
        "You are a factual-accuracy assistant.  A previous answer to the "
        "user's question contained hallucinations and must be rewritten.\n"
    )

    # ── Original question ────────────────────────────────────────────
    sections.append(f"## Original Question\n{question}\n")

    # ── Failed answer ────────────────────────────────────────────────
    sections.append(f"## Previous (Failed) Answer\n{failed_answer}\n")

    # ── Contradicted claims ──────────────────────────────────────────
    if contradicted_claims:
        items = "\n".join(f"- {c}" for c in contradicted_claims)
        sections.append(
            f"## Contradicted Claims\n"
            f"The following claims were **contradicted** by trusted evidence:\n{items}\n"
        )

    # ── Unsupported claims ───────────────────────────────────────────
    if unsupported_claims:
        items = "\n".join(f"- {c}" for c in unsupported_claims)
        sections.append(
            f"## Unsupported Claims\n"
            f"The following claims could **not be verified** (no supporting evidence):\n{items}\n"
        )

    # ── Trusted evidence ─────────────────────────────────────────────
    if evidence:
        evidence_lines: list[str] = []
        for idx, ev in enumerate(evidence, 1):
            snippet = ev.get("snippet", "")
            source = ev.get("source", "unknown")
            url = ev.get("url", "")
            line = f"{idx}. [{source}] {snippet}"
            if url:
                line += f"  ({url})"
            evidence_lines.append(line)
        evidence_block = "\n".join(evidence_lines)
        sections.append(f"## Trusted Evidence\n{evidence_block}\n")

    # ── Instructions ─────────────────────────────────────────────────
    sections.append(
        "## Instructions\n"
        "Rewrite the answer to the original question using ONLY the trusted "
        "evidence provided above.  Follow these rules:\n"
        "1. Do NOT include any claim that is not directly supported by the evidence.\n"
        "2. Remove or correct every contradicted claim.\n"
        "3. If the evidence is insufficient to answer part of the question, "
        "explicitly state that the information is unavailable.\n"
        "4. Keep the answer concise, accurate, and well-structured.\n"
        "5. Do NOT add any information beyond what the evidence supports.\n"
    )

    return "\n".join(sections)
