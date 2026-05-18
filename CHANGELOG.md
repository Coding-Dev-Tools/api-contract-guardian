# Changelog

All notable changes to API Contract Guardian will be documented in this file.

## [Unreleased]

### Added

- MCP server integration via `mcp` subcommand (#6)
- GitHub Pages deployment workflow (`pages.yml`)
- npm-publish workflow for npm publishing
- `package.json` with npm discoverability keywords (15 keywords)
- CLI test suite: 136 tests covering all subcommands (check, diff, migrate, mcp, gate)
- `SECURITY.md` with reporting guidelines
- `CONTRIBUTING.md` with development setup and contribution workflow
- Homebrew and Scoop install methods
- Directory listing badges: Open Source Alternative, LibHunt, Awesome Python
- CI badge and project health badges (GitHub release, Python version, license)
- Beta badge and star CTA in README header
- `revenueholdings-license` gating on all CLI commands
- GitHub-based install fallback (`pip install git+https://...`)
- `ruff` to dev dependencies for CI lint step

### Changed

- CLI command names: `gate` → `check`, features table updated to `diff, check, migrate`
- Pricing tool count updated from 8 to 11 (DevForge suite expansion)
- CI security hardened, `npm-publish.yml` removed
- `actions/checkout` pinned to `@v4` (v6 caused workflow parse failures)
- README restructured with unified pricing, Revenue Holdings branding, benefit-positive language
- Author metadata updated to Revenue Holdings
- GitHub project URLs added to pyproject.toml

### Fixed

- Escaped dollar signs (`\$`) in publish workflow YAML
- README code block formatting (broken fences)
- UTF-8 encoding issues in source files
- MCP command: license check moved outside docstring to work correctly
- `__pycache__` directories removed from git tracking; `.gitignore` corrected
- Ruff lint issues: `datetime.UTC`, `X | None` syntax, `E501` line length, `B904` exception chaining, `F821` undefined names
- CI trigger branch corrected from `master` to `main`
- PyPI badges replaced with GitHub release badge (package not yet on PyPI)
- BOM (byte order mark) removed from config files
- `revenueholdings-license` import made optional to fix CI failures on open-source PRs

## [0.1.0] — 2026-05-14

### Added

- Initial release
- Breaking change detection: removed endpoints, changed types, renamed fields, removed properties, required property additions, response format changes
- OpenAPI 3.0.x and 3.1.x support
- Git branch, tag, and commit diffing
- Local file comparison mode
- Human-readable markdown migration guide generation
- CI gating with non-zero exit on breaking changes
- Python 3.10+ support
