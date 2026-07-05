"""Core pipeline sub-package for TruthGuardAI.

Exports the main pipeline functions for:
- Claim extraction
- Evidence retrieval
- Citation checking
- Claim verification
- Report building
"""

from app.core.claim_extractor import extract_claims
from app.core.evidence_retriever import retrieve_candidate_evidence, retrieve_evidence
from app.core.citation_checker import check_citations
from app.core.verifier import verify_claims
from app.core.report_builder import build_report

__all__ = [
    "extract_claims",
    "retrieve_candidate_evidence",
    "retrieve_evidence",
    "check_citations",
    "verify_claims",
    "build_report",
]
