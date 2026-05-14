# API Contract Guardian

Catch breaking API changes in CI before they reach your consumers. API Contract Guardian monitors OpenAPI schema diffs between git branches, detects breaking changes, generates migration guides, and gates CI pipelines on contract violations.

[![PyPI](https://img.shields.io/pypi/v/api-contract-guardian)](https://pypi.org/project/api-contract-guardian/)
[![Python](https://img.shields.io/pypi/pyversions/api-contract-guardian)](https://pypi.org/project/api-contract-guardian/)
[![License](https://img.shields.io/pypi/l/api-contract-guardian)](https://github.com/Coding-Dev-Tools/api-contract-guardian/blob/main/LICENSE)

**Why API Contract Guardian?** API contracts define trust between services. When they break silently, every consumer — mobile apps, partner integrations, your own frontend — gets broken too. ACG catches contract violations in CI, pinpoints exactly what changed, and auto-generates migration guides so your consumers can adapt immediately. Works with OpenAPI 3.0.x and 3.1.x.

## Features

- **Breaking Change Detection**: Identifies removed endpoints, changed types, renamed fields, removed properties, and more
- **Migration Guide Generation**: Produces human-readable markdown migration guides
- **CI Gating**: Exits with non-zero code when breaking changes are detected
- **OpenAPI 3.x Support**: Full support for OpenAPI 3.0.x and 3.1.x specs
- **Git Branch Diffing**: Compare specs between branches, tags, or commits
- **File Comparison**: Compare two local spec files directly

## Installation

```bash
pip install api-contract-guardian
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

## Breaking Changes Detected

| Category | Example |
|----------|---------|
| Removed endpoint | `DELETE /users/{id}` removed |
| Removed property | `email` removed from `User` schema |
| Changed type | `age` changed from `integer` to `string` |
| Required property added | `phone` now required in `User` |
| Renamed field | `name` renamed to `fullName` |
| Response format changed | `200` response type changed |

## Pricing

One license covers all Revenue Holdings CLI tools. Pricing is per-seat.

| Tier | Price | Best For |
|------|-------|----------|
| **Open Source** | $0 | Individual devs, OSS projects — CLI only, local runs |
| **Pro** | **$29/mo** ($23 billed annually) | Professional devs — CI/CD integration, API access, 5 projects |
| **Team** | **$79/mo** ($63 billed annually) | Teams up to 5 — dashboards, Slack alerts, priority support |
| **Enterprise** | **$199/mo** (custom) | Organizations — SSO/SAML, RBAC, dedicated support, SLA |

🔹 **No lock-in**: CLI works fully offline on the free tier — no telemetry, no phone-home.  
🔹 **Annual billing**: Save 20%.  
🔹 **Education / OSS**: Free Pro tier for verified students and open-source projects.  

### What's in each tier?

| Feature | OSS | Pro | Team | Enterprise |
|---------|:---:|:---:|:----:|:----------:|
| CLI: check, migrate, gate | ✓ | ✓ | ✓ | ✓ |
| Custom rules & policies | — | ✓ | ✓ | ✓ |
| CI/CD integration (GitHub Actions, etc.) | — | ✓ | ✓ | ✓ |
| Multi-repo monitoring | — | 1 repo | 5 repos | Unlimited |
| Priority email support | Community | 24h | 8h | Dedicated |
| SSO / SAML / OIDC | — | — | — | ✓ |
| Uptime SLA | — | — | 99.5% | 99.9% |

---

<p align="center">
  <sub>Part of <a href="https://coding-dev-tools.github.io/revenueholdings.dev/">Revenue Holdings</a> — CLI tools built by autonomous AI.</sub>
</p>

## License

MIT
