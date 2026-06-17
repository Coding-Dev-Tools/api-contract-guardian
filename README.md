# API Contract Guardian

[![GitHub stars](https://img.shields.io/github/stars/Coding-Dev-Tools/api-contract-guardian?style=social)](https://github.com/Coding-Dev-Tools/api-contract-guardian/stargazers)

Monitor OpenAPI schema diffs between git branches, detect breaking changes, generate migration guides, and block CI pipelines on contract violations.
|[![CI](https://github.com/Coding-Dev-Tools/api-contract-guardian/actions/workflows/ci.yml/badge.svg)](https://github.com/Coding-Dev-Tools/api-contract-guardian/actions)

> ⭐ **Star this repo** if you maintain APIs — it helps other devs discover API Contract Guardian!

|[![GitHub release](https://img.shields.io/github/v/release/Coding-Dev-Tools/api-contract-guardian?label=latest)](https://github.com/Coding-Dev-Tools/api-contract-guardian/releases)
|![Python](https://img.shields.io/badge/python-3.10%2B-blue)
|[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/Coding-Dev-Tools/api-contract-guardian/blob/main/LICENSE)
|[![Open Source Alternative](https://img.shields.io/badge/Open_Source_Alternative-%E2%87%92-blue?logo=opensourceinitiative)](https://www.opensourcealternative.to/project/api-contract-guardian)
|[![LibHunt](https://img.shields.io/badge/LibHunt-%E2%87%92-blue?logo=codeigniter)](https://www.libhunt.com/r/Coding-Dev-Tools/api-contract-guardian)
|[![PyPI](https://img.shields.io/pypi/v/api-contract-guardian)](https://pypi.org/project/api-contract-guardian/)

**Why API Contract Guardian?**

Real-world scenarios:
- **CI/CD gating**: Block PRs that introduce breaking API changes — catch them before merge, not after deploy
- **API version upgrades**: When bumping v1 → v2, generate a migration guide for consumers automatically
- **Microservice contract enforcement**: Ensure service boundaries respect their OpenAPI contracts across deploys
- **Client SDK regeneration**: Know exactly what changed so SDK clients can be updated with confidence

## Installation

```bash
pip install api-contract-guardian
```

Or install the latest version directly from GitHub:

```bash
pip install git+https://github.com/Coding-Dev-Tools/api-contract-guardian.git
```

Or install via Homebrew (macOS/Linux):

```bash
brew tap Coding-Dev-Tools/tap
brew install api-contract-guardian
```

Or install via Scoop (Windows):

```bash
scoop bucket add Coding-Dev-Tools https://github.com/Coding-Dev-Tools/scoop-bucket
scoop install api-contract-guardian
```

**npm (Node.js wrapper — publishing pending):**

```bash
# Not yet available — install via pip instead
```

Then run: `api-contract-guardian --help`
## Quick Start

```bash
# Compare two spec files
api-contract-guardian check spec-v1.yaml spec-v2.yaml

# Generate migration guide
api-contract-guardian migrate spec-v1.yaml spec-v2.yaml --output MIGRATION.md

# CI gating (exits non-zero on breaking changes)
api-contract-guardian check spec-v1.yaml spec-v2.yaml
```

For machine-readable output, use --format yaml or --format json.

Example commands:

api-contract-guardian check spec-v1.yaml spec-v2.yaml --format yaml --output contract-diff.yaml

api-contract-guardian migrate spec-v1.yaml spec-v2.yaml --format json --output MIGRATION.json

## Features

- **Breaking Change Detection**: Identifies removed endpoints, changed types, renamed fields, removed properties, and more
- **Migration Guide Generation**: Produces human-readable markdown migration guides
- **Multiple Output Formats**: Rich (terminal), JSON, YAML, or Markdown for `diff` and `migrate`; Rich, JSON, or YAML for `check`
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
api-contract-guardian check spec-v1.yaml spec-v2.yaml || echo "Breaking API changes found!"
```

## Pricing

API Contract Guardian is one of eleven tools in the Revenue Holdings suite. One license covers all CLI tools.

| Plan | Price | Best For |
|------|-------|----------|
| **Free** | $0 | Individual devs, OSS — CLI only, 1 spec comparison |
| **ACG Individual** | **$19/mo** ($15 billed annually) | Professional devs — unlimited specs, CI/CD gating |
| **Suite (all 11 tools)** | **$49/mo** ($39 billed annually) | Full Revenue Holdings toolkit — 40% savings |
| **Team** | **$79/mo** ($63 billed annually) | Up to 5 devs — shared dashboards, alerts, run history |
| **Enterprise** | Custom | SSO, RBAC, compliance reports, dedicated support |

🔹 **No lock-in**: CLI works fully offline on the free tier — no telemetry, no phone-home.
🔹 **Annual billing**: Save 20%.

### Per-Tier Features

| Feature | Free | ACG | Suite | Team | Enterprise |
|---------|:----:|:---:|:-----:|:----:|:----------:|
| CLI: diff, check, migrate | ✓ | ✓ | ✓ | ✓ | ✓ |
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
  <sub>Part of <a href="https://coding-dev-tools.github.io/devforge/">Revenue Holdings</a> — CLI tools built by autonomous AI.</sub>
</p>

## License

MIT
