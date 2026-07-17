# Grounded AI

Grounded AI is a small local-first repository for experimenting with grounded verification of LLM outputs. It contains the following sub-projects:

- `truthbench`: an evaluation toolkit for measuring hallucination-verification behavior against labeled datasets.
- `truthguard-ai`: a FastAPI service that extracts claims from generated answers, retrieves evidence, verifies claims, and returns a hallucination-risk report.
- `prompt-shield`: an LLM security proxy for PII scrubbing, prompt injection detection, and toxicity filtering.
- `auto-grounder`: an automated remediation pipeline that closes the loop by auto-correcting hallucinated outputs.

The prompt-level names `truth-bench` and `truth-guard` map to the actual folders `truthbench` and `truthguard-ai` in this repository.

## Repository Structure

```text
grounded-ai/
|-- README.md
|-- .gitignore
|-- truthbench/
|   |-- README.md
|   |-- pyproject.toml
|   |-- requirements.txt
|   |-- .env.example
|   |-- config.py
|   |-- runner.py
|   |-- reporter.py
|   |-- metrics.py
|   |-- schemas.py
|   |-- datasets/
|   |   |-- README.md
|   |   |-- dataset_schema.md
|   |   `-- sample_eval_dataset.json
|   |-- evaluators/
|   |-- scripts/
|   `-- tests/
`-- truthguard-ai/
    |-- README.md
    |-- pyproject.toml
    |-- requirements.txt
    |-- .env.example
    |-- app/
    |   |-- main.py
    |   |-- config.py
    |   |-- schemas.py
    |   |-- api/
    |   |-- core/
    |   |-- services/
    |   `-- utils/
    |-- docs/
    |-- examples/
    `-- tests/
```

Generated files and local-only folders such as `.venv/`, `.pytest_cache/`, `__pycache__/`, and `truthbench/reports/` are ignored and are not required source files.

For a detailed annotated directory tree, see [DIRECTORY_STRUCTURE.md](./DIRECTORY_STRUCTURE.md).

## Setup

Use Python 3.11 or newer.

Install Truth Bench dependencies:

```bash
python -m pip install -r truthbench/requirements.txt
```

Install Truth Guard dependencies:

```bash
python -m pip install -r truthguard-ai/requirements.txt
```

For isolated development, create a virtual environment first:

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

On macOS or Linux, activate with `source .venv/bin/activate`.

## How To Run

Run the Truth Bench sample benchmark from the repository root:

```bash
python -m truthbench.scripts.run_truthbench
```

The command writes `truthbench/reports/generated_evaluation_report.md`. It exits with status `1` when any benchmark case fails, which is expected for the current mock benchmark because one case intentionally exposes an over-extraction issue.

Run the Truth Guard API:

```bash
cd truthguard-ai
python -m uvicorn app.main:app --reload
```

Then open `http://127.0.0.1:8000/docs` or check:

```bash
curl http://127.0.0.1:8000/health
```

## Dependencies

Truth Bench uses `pydantic`, `pydantic-settings`, `python-dotenv`, `pytest`, and `pytest-asyncio`.

Truth Guard uses `fastapi`, `uvicorn`, `pydantic`, `pydantic-settings`, `python-dotenv`, `pytest`, `pytest-asyncio`, and `httpx`.

Optional production-facing packages are listed in `truthguard-ai/pyproject.toml`, but the current runnable code paths use mock providers.

## Configuration

Both subprojects include `.env.example` files. Copy the relevant file to `.env` only when you need local overrides.

Truth Bench supports dataset path, verdict labels, risk levels, confidence threshold, deterministic evaluation seed, report output directory, report format, and logging level.

Truth Guard supports app metadata, provider selection, API key placeholders, trusted source defaults, and verification limits. Mock providers are the only complete provider path today.

Do not commit real `.env` files, API keys, tokens, or credentials.

## Example Usage

Truth Bench:

```bash
python -m truthbench.scripts.run_truthbench
```

Truth Guard request:

```bash
curl -X POST http://127.0.0.1:8000/verify ^
  -H "Content-Type: application/json" ^
  -d "{\"original_question\":\"What is the population of France?\",\"generated_answer\":\"France has a population of approximately 68 million people in 2023. Paris is the capital of France.\",\"trusted_sources\":[\"wikipedia\",\"world-bank\"]}"
```

## Testing

Run all included tests from the repository root:

```bash
python -m pytest truthbench/tests truthguard-ai/tests -v
```

Run individual suites:

```bash
python -m pytest truthbench/tests -v
python -m pytest truthguard-ai/tests -v
```

Tests are included for both projects. Broader integration tests could be added for the FastAPI `/verify` route and for running Truth Bench against Truth Guard directly.

## Development Notes

- There is no root Python package yet; the two subprojects are installed and run independently.
- `truthbench` is importable from the repository root as a package directory.
- `truthguard-ai` uses `app` imports, so run its API from inside `truthguard-ai`.
- The root `main.py` file was a default PyCharm sample and has been removed.
- Root temporary audit and generated sample/report artifacts were removed because they were not project source files.

## Improvement Roadmap

- Add a root workspace or tooling file if both projects should be installed and tested as one unit.
- Add a Truth Bench adapter that evaluates Truth Guard directly.
- Implement real LLM and search clients behind Truth Guard's existing service interfaces.
- Add FastAPI integration tests for `POST /verify`.
- Expand Truth Bench with larger domain-specific and adversarial datasets.
- Add a repository license file if MIT is the intended license.

## License

License not specified. The subproject package metadata declares MIT, but this repository does not currently include a license file.
