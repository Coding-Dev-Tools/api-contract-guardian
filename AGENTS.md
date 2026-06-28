# API Contract Guardian — Agent Instructions

## Repository Overview
**API Contract Guardian** — CLI tool that monitors OpenAPI schema diffs, detects breaking changes, generates migration guides, and gates CI pipelines on contract violations.

- **Owner**: Revenue Holdings / Coding-Dev-Tools
- **Type**: CLI Tool (Tier 2 — Developer Tools)
- **Language**: Python 3.10+
- **License**: MIT

## Build & Test Commands

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
python -m pytest tests/ -v --tb=short

# Lint with ruff
ruff check src/ tests/ --target-version py310

# Fix linting issues
ruff check src/ tests/ --target-version py310 --fix

# Run CLI
api-contract-guardian --help
```

## CI Pipeline
- **File**: `.github/workflows/ci.yml`
- **Matrix**: Python 3.10, 3.11, 3.12, 3.13
- **Steps**: Install → Lint (ruff) → Tests (pytest) → CLI smoke test

## Key Files
- `src/api_contract_guardian/cli.py` — Typer CLI entry point
- `src/api_contract_guardian/diff.py` — Core diff engine
- `src/api_contract_guardian/gate.py` — CI gating logic
- `src/api_contract_guardian/loader.py` — Spec loading & validation
- `src/api_contract_guardian/migration.py` — Migration guide generation

## Common Fixes
- **ruff I001**: Import blocks un-sorted → run `ruff check --fix`
- **ruff B904**: Exception re-raise without `from` → use `raise ... from err` or `raise ... from None`
- **Missing AGENTS.md**: Create this file

## Version & Release
- Version in `pyproject.toml` `[project].version`
- Release via `.github/workflows/publish.yml` (triggers on version tag)
- Changelog in `CHANGELOG.md`

## Architecture Notes
- Lazy imports in CLI commands to avoid heavy deps (jwt, cryptography, deepdiff, yaml) at module level
- License check via `revenueholdings_license` (optional dependency)
- OpenAPI 3.0.x and 3.1.x support

## Autonomous Operations
This repo is visited by the dev-engineer cron job on a 32-repo rotation. The agent should:
1. Check for CI failures (ruff, tests)
2. Fix linting issues (max 50 lines changed)
3. Create PR with improvements
4. Advance rotation pointer# Trigger CI
