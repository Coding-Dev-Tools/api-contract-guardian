# API Contract Guardian

Monitor OpenAPI schema diffs between git branches, detect breaking changes, generate migration guides, and block CI pipelines on contract violations.

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

One license covers all Revenue Holdings CLI tools. Pricing is per-seat.

| Tier | Price | Best For |
|------|-------|----------|
| **Open Source** | $0 | Individual devs, OSS projects — CLI only, limited checks |
| **Pro** | **$29/mo** ($23 billed annually) | Professional devs — unlimited checks, custom rules |
| **Team** | **$79/mo** ($63 billed annually) | Teams up to 5 — CI/CD integrations, team dashboard |
| **Enterprise** | **$199/mo** (custom) | Organizations — compliance reports, RBAC, SSO, SLA |

🔹 **No lock-in**: CLI works fully offline on the free tier — no telemetry, no phone-home.  
🔹 **Annual billing**: Save 20%.

### Per-Tier Features

| Feature | OSS | Pro | Team | Enterprise |
|---------|:---:|:---:|:----:|:----------:|
| CLI: check, migrate, gate | ✓ | ✓ | ✓ | ✓ |
| Unlimited API checks | — | ✓ | ✓ | ✓ |
| Custom rules / policies | — | ✓ | ✓ | ✓ |
| Team dashboard | — | — | ✓ | ✓ |
| Compliance reports | — | — | — | ✓ |
| RBAC | — | — | — | ✓ |
| SSO / SAML / OIDC | — | — | — | ✓ |
| Priority support | Community | 24h | 8h | Dedicated |

---

<p align="center">
  <sub>Part of <a href="https://coding-dev-tools.github.io/revenueholdings.dev/">Revenue Holdings</a> — CLI tools built by autonomous AI.</sub>
</p>

## License

MIT
