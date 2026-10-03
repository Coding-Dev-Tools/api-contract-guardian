# API Contract Guardian

## Purpose
CLI tool that monitors OpenAPI schema diffs, detects breaking changes, generates migration guides, and gates CI pipelines on contract violations.

## Build & Test Commands
- Install: `pip install -e .` or `pip install git+https://github.com/Coding-Dev-Tools/api-contract-guardian.git`
- Test: `pytest` 
- Lint: `ruff check .`
- Build: `pip wheel . --wheel-dir dist/`

## Architecture
Key directories:
- `src/api_contract_guardian/` — Main package (CLI, diff engine, migration guide generator)
- `tests/` — Test suite
- `.github/workflows/` — CI/CD (4 workflows)

## Conventions
- Language: Python 3.10+
- Test framework: pytest
- CI: GitHub Actions (4 workflows)
- Formatting: ruff (line-length 120)
- Type checking: py.typed included
- Package: setuptools with src layout
- CLI framework: typer