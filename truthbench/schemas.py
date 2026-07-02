"""Pydantic models for TruthBench evaluation dataset and results."""
from __future__ import annotations

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class Verdict(str, Enum):
    """Possible verification verdicts for a single claim."""
    SUPPORTED = "SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    NOT_ENOUGH_EVIDENCE = "NOT_ENOUGH_EVIDENCE"


class RiskLevel(str, Enum):
    """Aggregate hallucination risk level."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ExpectedClaim(BaseModel):
    """A claim that should be extracted from the generated answer."""
    text: str = Field(..., description="The expected claim text")
    claim_type: str = Field(default="factual", description="Type of claim: factual, statistical, causal, definitional")


class ExpectedVerdict(BaseModel):
    """Expected verdict for a specific claim."""
    claim_text: str = Field(..., description="The claim text this verdict applies to")
    verdict: Verdict = Field(..., description="Expected verdict")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Expected confidence")
    reasoning: str = Field(default="", description="Expected reasoning")


class EvaluationCase(BaseModel):
    """A single evaluation test case."""
    id: str = Field(..., description="Unique identifier for this test case")
    original_question: str = Field(..., description="The original user question")
    generated_answer: str = Field(..., description="The LLM-generated answer to evaluate")
    expected_claims: List[ExpectedClaim] = Field(default_factory=list, description="Claims that should be extracted")
    expected_verdicts: List[ExpectedVerdict] = Field(default_factory=list, description="Expected verdicts for each claim")
    trusted_reference_evidence: List[str] = Field(default_factory=list, description="Reference evidence sources")
    expected_risk_level: RiskLevel = Field(..., description="Expected overall risk level")
    notes: str = Field(default="", description="Additional notes about this test case")


class EvaluationDataset(BaseModel):
    """Complete evaluation dataset."""
    name: str = Field(default="TruthBench Evaluation Dataset", description="Dataset name")
    version: str = Field(default="0.1.0", description="Dataset version")
    description: str = Field(default="", description="Dataset description")
    cases: List[EvaluationCase] = Field(..., description="List of evaluation cases")


# Prediction models (what the system under test produces)

class PredictedClaim(BaseModel):
    """A claim extracted by the system under test."""
    text: str = Field(..., description="Extracted claim text")
    start_index: int = Field(default=0, ge=0)
    end_index: int = Field(default=0, ge=0)
    claim_type: str = Field(default="factual")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class PredictedVerdict(BaseModel):
    """A verdict predicted by the system under test."""
    claim_text: str = Field(..., description="The claim this verdict applies to")
    verdict: Verdict = Field(..., description="Predicted verdict")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence_indices: List[int] = Field(default_factory=list)
    reasoning: str = Field(default="")


class PredictedResult(BaseModel):
    """Complete prediction result from the system under test."""
    case_id: str = Field(..., description="ID of the evaluation case")
    extracted_claims: List[PredictedClaim] = Field(default_factory=list)
    predicted_verdicts: List[PredictedVerdict] = Field(default_factory=list)
    hallucination_risk_score: float = Field(default=0.0, ge=0.0, le=1.0)
    risk_level: RiskLevel = Field(default=RiskLevel.LOW)
    citations: List[str] = Field(default_factory=list)
    processing_time_ms: int = Field(default=0)


# Evaluation result models

class CaseEvaluationResult(BaseModel):
    """Evaluation result for a single test case."""
    case_id: str
    claim_accuracy: float = Field(..., ge=0.0, le=1.0)
    verdict_accuracy: float = Field(..., ge=0.0, le=1.0)
    verdict_precision: float = Field(..., ge=0.0, le=1.0)
    verdict_recall: float = Field(..., ge=0.0, le=1.0)
    verdict_f1: float = Field(..., ge=0.0, le=1.0)
    hallucination_rate: float = Field(..., ge=0.0, le=1.0)
    citation_coverage: float = Field(..., ge=0.0, le=1.0)
    risk_level_match: bool
    failed_checks: List[str] = Field(default_factory=list)


class AggregateEvaluationResult(BaseModel):
    """Aggregated evaluation results across all test cases."""
    total_cases: int
    total_claims_evaluated: int
    mean_claim_accuracy: float
    mean_verdict_accuracy: float
    mean_verdict_precision: float
    mean_verdict_recall: float
    mean_verdict_f1: float
    mean_hallucination_rate: float
    mean_citation_coverage: float
    risk_level_match_rate: float
    passed_cases: int
    failed_cases: int
    case_results: List[CaseEvaluationResult]
    recommendations: List[str] = Field(default_factory=list)


class EvaluationReport(BaseModel):
    """Complete evaluation report."""
    dataset_name: str
    dataset_version: str
    aggregate_results: AggregateEvaluationResult
    generated_at: str
    runner_version: str = "0.1.0"