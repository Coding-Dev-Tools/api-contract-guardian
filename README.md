# API Contract Guardian

[![GitHub stars](https://img.shields.io/github/stars/Coding-Dev-Tools/api-contract-guardian?style=social)](https://github.com/Coding-Dev-Tools/api-contract-guardian/stargazers)

Monitor OpenAPI schema diffs between git branches, detect breaking changes, generate migration guides, and block CI pipelines on contract violations.

> ⭐ **Star this repo** if you maintain APIs — it helps other devs discover API Contract Guardian!

[![PyPI](https://img.shields.io/pypi/v/api-contract-guardian)](https://pypi.org/project/api-contract-guardian/)
[![Python](https://img.shields.io/pypi/pyversions/api-contract-guardian)](https://pypi.org/project/api-contract-guardian/)
[![License](https://img.shields.io/pypi/l/api-contract-guardian)](https://github.com/Coding-Dev-Tools/api-contract-guardian/blob/main/LICENSE)

**Why API Contract Guardian?** APIs evolve fast, and breaking changes slip into production when the team reviewing the PR doesn't know every detail of every endpoint. API Contract Guardian catches removed endpoints, changed types, renamed fields, and missing required properties at PR time — not after deploy. It generates human-readable migration guides so your API consumers aren't left guessing. Works with OpenAPI 3.0.x and 3.1.x, integrates into CI with a single non-zero exit, and compares specs across branches, tags, commits, or local files.

## Installation

```bash
pip install api-contract-guardian
```

Or install directly from GitHub:

```bash
pip install git+https://github.com/Coding-Dev-Tools/api-contract-guardian.git
```

## Quick Start

```bash
# Compare two spec files
api-contract-guardian check spec-v1.yaml spec-v2.yaml

# Compare git branches
api-contract-guardian check --base main --head feature-api-v2 openapi.yaml

# Generate migration guide
api-contract-guardian migrate spec-v1.yaml spec-v2.yaml --output MIGRATION.md

# CI gating (exits non-zero on breaking changes)
api-contract-guardian gate spec-v1.yaml spec-v2.yaml
```

## Features

- **Breaking Change Detection**: Identifies removed endpoints, changed types, renamed fields, removed properties, and more
- **Migration Guide Generation**: Produces human-readable markdown migration guides
- **CI Gating**: Exits with non-zero code when breaking changes are detected
- **OpenAPI 3.x Support**: Full support for OpenAPI 3.0.x and 3.1.x specs
- **Git Branch Diffing**: Compare specs between branches, tags, or commits
- **File Comparison**: Compare two local spec files directly

## Breaking Changes Detected

| Category | Example |
|----------|---------|
| Removed endpoint | `DELETE /users/{id}` removed |
| Removed property | `email` removed from `User` schema |
| Changed type | `age` changed from `integer` to `string` |
| Required property added | `phone` now required in `User` |
| Renamed field | `name` renamed to `fullName` |
| Response format changed | `200` response type changed |

## CI/CD Integration

```bash
# Fail the build if breaking changes are detected
api-contract-guardian gate spec-v1.yaml spec-v2.yaml || echo "Breaking API changes found!"
```

## Pricing

API Contract Guardian is one of eight tools in the Revenue Holdings suite. One license covers all CLI tools.

| Plan | Price | Best For |
|------|-------|----------|
| **Free** | $0 | Individual devs, OSS — CLI only, 1 spec comparison |
| **ACG Individual** | **$19/mo** ($15 billed annually) | Professional devs — unlimited specs, CI/CD gating |
| **Suite (all 8 tools)** | **$49/mo** ($39 billed annually) | Full Revenue Holdings toolkit — 40% savings |
| **Team** | **$79/mo** ($63 billed annually) | Up to 5 devs — shared dashboards, alerts, run history |
| **Enterprise** | Custom | SSO, RBAC, compliance reports, dedicated support |

🔹 **No lock-in**: CLI works fully offline on the free tier — no telemetry, no phone-home.
🔹 **Annual billing**: Save 20%.

### Per-Tier Features

| Feature | Free | ACG | Suite | Team | Enterprise |
|---------|:----:|:---:|:-----:|:----:|:----------:|
| CLI: check, gate, migrate | ✓ | ✓ | ✓ | ✓ | ✓ |
| Unlimited spec comparisons | — | ✓ | ✓ | ✓ | ✓ |
| CI/CD gating | — | ✓ | ✓ | ✓ | ✓ |
| Migration guide generation | — | ✓ | ✓ | ✓ | ✓ |
| Custom rules / policies | — | ✓ | ✓ | ✓ | ✓ |
| Team dashboard | — | — | — | ✓ | ✓ |
| Compliance reports | — | — | — | — | ✓ |
| RBAC | — | — | — | — | ✓ |
| SSO / SAML / OIDC | — | — | — | — | ✓ |
| Priority support | Community | 24h | 24h | 8h | Dedicated |

<p align="center">
  <sub>Part of <a href="https://coding-dev-tools.github.io/revenueholdings.dev/">Revenue Holdings</a> — CLI tools built by autonomous AI.</sub>
</p>

## License

MIT
