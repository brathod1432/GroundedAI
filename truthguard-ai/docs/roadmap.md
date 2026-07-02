# Roadmap

## Vision

Build the most trustworthy, production-ready hallucination reduction framework for LLM applications — a verification layer that makes every AI answer accountable to evidence.

## Version History

### v0.1 — Foundation (Current)
**Status**: ✅ Complete

- [x] Modular pipeline architecture (extractor → retriever → verifier → scorer → report)
- [x] Pydantic-validated request/response schemas
- [x] FastAPI endpoint with auto-generated docs
- [x] Mock LLM and Search backends (zero-config dev)
- [x] Keyword-overlap verification with 3-way verdicts
- [x] Weighted risk scoring (LOW/MEDIUM/HIGH)
- [x] Citation validation
- [x] Comprehensive unit tests (24 tests passing)
- [x] TruthBench evaluation framework (48 tests passing)
- [x] Professional documentation (architecture, strategy, API, evaluation)

### v0.2 — Real LLM Integration
**Target**: Q2 2025

- [ ] OpenAI client implementation (chat completions, structured output)
- [ ] Anthropic client implementation
- [ ] LLM-based claim extractor (replaces rule-based)
- [ ] LLM-based claim verifier (chain-of-thought reasoning)
- [ ] Confidence calibration with temperature scaling
- [ ] Structured output parsing (JSON mode)
- [ ] Cost tracking per verification request

### v0.3 — Real Search Integration
**Target**: Q2 2025

- [ ] Tavily search client
- [ ] Wikipedia API client
- [ ] SerpAPI client
- [ ] Source credibility weighting
- [ ] Multi-source evidence fusion
- [ ] Temporal filtering (recency-aware)
- [ ] Domain-specific source packs (medical, legal, financial)

### v0.4 — Citation & Source Quality
**Target**: Q3 2025

- [ ] URL validation and accessibility checking
- [ ] Citation format validation (APA, IEEE, etc.)
- [ ] Source authority scoring
- [ ] Duplicate evidence deduplication
- [ ] Evidence span highlighting (exact supporting sentences)
- [ ] Citation graph visualization

### v0.5 — Batch & Streaming
**Target**: Q3 2025

- [ ] Batch verification endpoint (`POST /verify/batch`)
- [ ] Async streaming responses for long answers
- [ ] Webhook/callback for async completion
- [ ] Request deduplication (cache identical questions)
- [ ] Priority queue for latency-sensitive requests

### v0.6 — Calibration & Evaluation
**Target**: Q4 2025

- [ ] Human-labeled evaluation set (1000+ cases)
- [ ] Threshold optimization (isotonic regression / Platt scaling)
- [ ] Uncertainty quantification (conformal prediction)
- [ ] Subgroup analysis (by domain, claim type, language)
- [ ] A/B testing framework for prompt/model variants

### v0.7 — Production Hardening
**Target**: Q4 2025

- [ ] Prometheus metrics exporter
- [ ] OpenTelemetry distributed tracing
- [ ] Structured logging (JSON, correlation IDs)
- [ ] Rate limiting and quota management
- [ ] Circuit breakers for external APIs
- [ ] Graceful degradation (fallback to HIGH risk on failure)
- [ ] Health checks: liveness, readiness, dependency

### v1.0 — Production Release
**Target**: Q1 2026

- [ ] Complete API stability (v1 schema freeze)
- [ ] Deployment guides (Docker, Kubernetes, serverless)
- [ ] Migration guide from v0.x
- [ ] Security audit (OWASP LLM Top 10)
- [ ] Performance benchmarks published
- [ ] Example integrations (LangChain, LlamaIndex, custom)
- [ ] Commercial support options documented

## Post-v1.0 Vision

### v1.1 — Advanced Reasoning
- Multi-hop verification (claim A → claim B → claim C)
- Numerical/statistical claim checking (exact value matching)
- Temporal reasoning (claims about time, trends, events)
- Counterfactual detection

### v1.2 — Domain Packs
- Medical: PubMed, FDA, clinical guidelines
- Legal: Case law, statutes, regulations
- Financial: SEC filings, central bank data, market data
- Scientific: arXiv, PubMed, patent databases

### v1.3 — Human-in-the-Loop
- Expert review workflow UI
- Active learning (flag uncertain cases for labeling)
- Feedback loop: user corrections → model improvement
- Audit trail for compliance

### v2.0 — Autonomous Verification
- Self-correcting pipeline (iterative refinement)
- Cross-model verification (ensemble of LLMs)
- Proactive fact-checking (pre-generation)
- Real-time streaming verification

## Technology Investments

| Area | Current | v1.0 Target |
|------|---------|-------------|
| Verification accuracy (macro F1) | ~0.71 | ≥ 0.85 |
| Hallucination detection recall | ~0.60 | ≥ 0.90 |
| False positive rate | ~0.15 | ≤ 0.05 |
| Latency (p95, mock) | ~500ms | < 200ms |
| Latency (p95, real APIs) | N/A | < 5s |
| Test coverage | 72 tests | > 200 tests |
| Documentation | 4 docs | 10+ guides |

## Dependencies & Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| LLM API cost at scale | High | Caching, batching, cheaper models for extraction |
| Search API rate limits | Medium | Multiple providers, local caching |
| Keyword overlap limitations | High | Embedding-based similarity in v0.4 |
| Domain coverage | Medium | Domain packs in v1.2 |
| Evaluation dataset bias | High | Diverse datasets, adversarial testing |

## Contribution Opportunities

- **Good first issues**: Add test cases, improve mock KB, doc improvements
- **Core**: LLM verifier, embedding similarity, calibration
- **Integrations**: LangChain, LlamaIndex, Haystack, custom
- **Domains**: Medical, legal, financial source packs
- **Ops**: Docker images, Helm charts, Terraform modules

## Release Process

1. **Feature branches** from `main`
2. **PR review** with CI (tests + TruthBench evaluation)
3. **Version bump** in `pyproject.toml` and `app/config.py`
4. **Changelog** entry in `CHANGELOG.md`
5. **GitHub Release** with artifacts
6. **Docker image** push to GHCR
7. **Docs deployment** to GitHub Pages

## Support Policy

| Version | Status | Support Until |
|---------|--------|---------------|
| 0.x | Alpha | Best effort |
| 1.x | Stable | 12 months after 2.x |
| 2.x | Stable | TBD |

---

*Last updated: 2025-01-07*