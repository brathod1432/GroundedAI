# Directory Structure

Complete directory tree for the GroundedAI monorepo. See the [root README](./README.md) for setup and usage instructions.

```
GroundedAI/
├── README.md                                       # Repository overview, setup, and usage
├── .gitignore                                      # Root-level git exclusions
│
├── prompt-shield/                                  # LLM Security Proxy (Planned)
│   └── README.md                                   #   Project concept and architecture
│
├── auto-grounder/                                  # Self-Healing Output Pipeline (Planned)
│   └── README.md                                   #   Project concept and architecture
│
├── truthbench/                                     # Evaluation toolkit for hallucination-reduction systems
│   ├── __init__.py                                 #   Package init (version, author metadata)
│   ├── config.py                                   #   Pydantic Settings configuration
│   ├── runner.py                                   #   Main evaluation orchestration (TruthBenchRunner)
│   ├── reporter.py                                 #   Report generation (Markdown and JSON)
│   ├── metrics.py                                  #   Shared metric functions (accuracy, F1, hallucination rate)
│   ├── schemas.py                                  #   Pydantic data models (cases, verdicts, results)
│   ├── pyproject.toml                              #   Project metadata, build config, linting rules
│   ├── requirements.txt                            #   Python dependencies
│   ├── .env.example                                #   Configuration template
│   ├── .gitignore                                  #   Sub-project git exclusions
│   ├── README.md                                   #   TruthBench documentation
│   ├── datasets/                                   #   Evaluation datasets
│   │   ├── README.md                               #     Dataset format and labeling guide
│   │   ├── dataset_schema.md                       #     JSON Schema reference
│   │   └── sample_eval_dataset.json                #     5-case sample evaluation dataset
│   ├── evaluators/                                 #   Evaluation modules
│   │   ├── __init__.py                             #     Package init
│   │   ├── citation_quality_evaluator.py           #     Citation coverage evaluation
│   │   ├── claim_accuracy_evaluator.py             #     Claim extraction accuracy (fuzzy matching)
│   │   ├── hallucination_risk_evaluator.py         #     Hallucination risk level evaluation
│   │   └── verdict_consistency_evaluator.py        #     Verdict prediction accuracy (macro F1)
│   ├── scripts/                                    #   CLI entry points
│   │   ├── __init__.py                             #     Package init
│   │   ├── run_truthbench.py                       #     Main benchmark runner
│   │   └── generate_sample_report.py               #     Sample report generator
│   └── tests/                                      #   Unit tests
│       ├── __init__.py                             #     Package init
│       ├── test_evaluators.py                      #     Evaluator tests
│       ├── test_metrics.py                         #     Metric function tests
│       └── test_runner.py                          #     Runner tests
│
└── truthguard-ai/                                  # FastAPI service for LLM output verification
    ├── README.md                                   #   TruthGuard documentation
    ├── pyproject.toml                              #   Project metadata, build config, linting rules
    ├── requirements.txt                            #   Python dependencies
    ├── .env.example                                #   Configuration template
    ├── .gitignore                                  #   Sub-project git exclusions
    ├── app/                                        #   Application package
    │   ├── __init__.py                             #     Package init
    │   ├── main.py                                 #     FastAPI application entry point
    │   ├── config.py                               #     Pydantic Settings configuration
    │   ├── schemas.py                              #     Request/response Pydantic models
    │   ├── api/                                    #     HTTP API layer
    │   │   ├── __init__.py                         #       Package init
    │   │   └── routes.py                           #       POST /verify, GET /health endpoints
    │   ├── core/                                   #     Verification pipeline modules
    │   │   ├── __init__.py                         #       Package init
    │   │   ├── claim_extractor.py                  #       Rule-based claim decomposition
    │   │   ├── evidence_retriever.py               #       Evidence fetching per claim
    │   │   ├── evidence_ranker.py                  #       Composite relevance ranking
    │   │   ├── claim_evidence_aligner.py           #       Jaccard-based claim-evidence alignment
    │   │   ├── citation_checker.py                 #       Citation validation (keyword overlap)
    │   │   ├── verifier.py                         #       Verdict assignment (SUPPORTED/CONTRADICTED/NEE)
    │   │   └── report_builder.py                   #       Final report assembly
    │   ├── services/                               #     External service integrations
    │   │   ├── __init__.py                         #       Package init
    │   │   ├── llm_client.py                       #       LLM client abstraction (mock, OpenAI, Anthropic)
    │   │   ├── search_client.py                    #       Search client abstraction (mock, Tavily, SerpAPI)
    │   │   └── scoring.py                          #       Risk score computation and risk level mapping
    │   └── utils/                                  #     Shared utilities
    │       ├── __init__.py                         #       Package init
    │       └── text_utils.py                       #       Text processing (sentence splitting, keywords)
    ├── docs/                                       #   Architecture and strategy documentation
    │   ├── api_design.md                           #     API design and endpoint documentation
    │   ├── architecture.md                         #     System architecture and pipeline design
    │   ├── evaluation_plan.md                      #     Evaluation metrics and quality gates
    │   ├── hallucination_reduction_strategy.md     #     Hallucination detection strategy
    │   └── roadmap.md                              #     Version roadmap (v0.1 → v1.0)
    ├── examples/                                   #   Sample request/response data
    │   ├── sample_input.json                       #     Example verification request
    │   └── sample_output.json                      #     Example verification response
    └── tests/                                      #   Unit and integration tests
        ├── __init__.py                             #     Package init
        ├── test_app.py                             #     API endpoint tests (health, verify)
        ├── test_claim_extractor.py                 #     Claim extraction tests
        ├── test_report_builder.py                  #     Report building tests
        ├── test_scoring.py                         #     Risk scoring tests
        ├── test_text_utils.py                      #     Text utility tests
        └── test_verifier.py                        #     Claim verification tests
```

## Verification Pipeline Flow

```
[POST /verify]
    │
    ▼
[1] Claim Extraction ─── claim_extractor.py
    │   Rule-based sentence splitting + factuality filtering
    ▼
[2] Evidence Retrieval ── evidence_retriever.py
    │   Per-claim search queries via search_client
    ▼
[3] Evidence Ranking ──── evidence_ranker.py
    │   Composite scoring: relevance + credibility + keywords
    ▼
[4] Claim-Evidence Alignment ── claim_evidence_aligner.py
    │   Jaccard similarity + contradiction detection
    ▼
[5] Citation Checking ─── citation_checker.py
    │   Keyword overlap validation for supported claims
    ▼
[6] Verification ──────── verifier.py
    │   Verdict assignment: SUPPORTED / CONTRADICTED / NOT_ENOUGH_EVIDENCE
    ▼
[7] Report Building ──── report_builder.py + scoring.py
    │   Risk score computation and final response assembly
    ▼
[VerifyResponse]
```
