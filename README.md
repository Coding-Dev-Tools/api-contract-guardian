# API Contract Guardian

[![GitHub stars](https://img.shields.io/github/stars/Coding-Dev-Tools/api-contract-guardian?style=social)](https://github.com/Coding-Dev-Tools/api-contract-guardian/stargazers)

Monitor OpenAPI schema diffs between git branches, detect breaking changes, generate migration guides, and block CI pipelines on contract violations.
n[![CI](https://github.com/Coding-Dev-Tools/api-contract-guardian/actions/workflows/ci.yml/badge.svg)](https://github.com/Coding-Dev-Tools/api-contract-guardian/actions)

> â­ **Star this repo** if you maintain APIs â€” it helps other devs discover API Contract Guardian!

[![GitHub release](https://img.shields.io/github/v/release/Coding-Dev-Tools/api-contract-guardian?label=latest)](https://github.com/Coding-Dev-Tools/api-contract-guardian/releases)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/Coding-Dev-Tools/api-contract-guardian/blob/main/LICENSE)
[![Open Source Alternative](https://img.shields.io/badge/Open_Source_Alternative-%E2%87%92-blue?logo=opensourceinitiative)](https://www.opensourcealternative.to/project/api-contract-guardian)
[![LibHunt](https://img.shields.io/badge/LibHunt-%E2%87%92-blue?logo=codeigniter)](https://www.libhunt.com/r/Coding-Dev-Tools/api-contract-guardian)
[![Awesome Python](https://img.shields.io/badge/Awesome_Python-%E2%87%92-blue?logo=python)](https://github.com/uhub/awesome-python)

**Why API Contract Guardian?** APIs evolve fast, and breaking changes slip into production when the team reviewing the PR doesn't know every detail of every endpoint. API Contract Guardian catches removed endpoints, changed types, renamed fields, and missing required properties at PR time â€” not after deploy. It generates human-readable migration guides so your API consumers aren't left guessing. Works with OpenAPI 3.0.x and 3.1.x, integrates into CI with a single non-zero exit, and compares specs across branches, tags, commits, or local files.

## Installation

```bash
pip install api-contract-guardian
```

Or install directly from GitHub:

```bash
pip install git+https://github.com/Coding-Dev-Tools/api-contract-guardian.git
nOr install via Homebrew (macOS/Linux):

```bash
brew tap Coding-Dev-Tools/tap
brew install api-contract-guardian
```

Or install via Scoop (Windows):

```bash
scoop bucket add Coding-Dev-Tools https://github.com/Coding-Dev-Tools/scoop-bucket
scoop install api-contract-guardian
```
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
| **Free** | $0 | Individual devs, OSS â€” CLI only, 1 spec comparison |
| **ACG Individual** | **$19/mo** ($15 billed annually) | Professional devs â€” unlimited specs, CI/CD gating |
| **Suite (all 8 tools)** | **$49/mo** ($39 billed annually) | Full Revenue Holdings toolkit â€” 40% savings |
| **Team** | **$79/mo** ($63 billed annually) | Up to 5 devs â€” shared dashboards, alerts, run history |
| **Enterprise** | Custom | SSO, RBAC, compliance reports, dedicated support |

ðŸ”¹ **No lock-in**: CLI works fully offline on the free tier â€” no telemetry, no phone-home.
ðŸ”¹ **Annual billing**: Save 20%.

### Per-Tier Features

| Feature | Free | ACG | Suite | Team | Enterprise |
|---------|:----:|:---:|:-----:|:----:|:----------:|
| CLI: check, gate, migrate | âœ“ | âœ“ | âœ“ | âœ“ | âœ“ |
| Unlimited spec comparisons | â€” | âœ“ | âœ“ | âœ“ | âœ“ |
| CI/CD gating | â€” | âœ“ | âœ“ | âœ“ | âœ“ |
| Migration guide generation | â€” | âœ“ | âœ“ | âœ“ | âœ“ |
| Custom rules / policies | â€” | âœ“ | âœ“ | âœ“ | âœ“ |
| Team dashboard | â€” | â€” | â€” | âœ“ | âœ“ |
| Compliance reports | â€” | â€” | â€” | â€” | âœ“ |
| RBAC | â€” | â€” | â€” | â€” | âœ“ |
| SSO / SAML / OIDC | â€” | â€” | â€” | â€” | âœ“ |
| Priority support | Community | 24h | 24h | 8h | Dedicated |

<p align="center">
  <sub>Part of <a href="https://coding-dev-tools.github.io/revenueholdings.dev/">Revenue Holdings</a> â€” CLI tools built by autonomous AI.</sub>
</p>

## License

MIT

