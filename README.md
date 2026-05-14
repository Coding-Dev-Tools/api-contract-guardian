# API Contract Guardian

A Python CLI tool that monitors OpenAPI schema diffs between git branches, detects breaking changes, generates migration guides, and can block CI pipelines on contract violations.

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

## Revenue Model

- Free: open-source projects
- Pro ($29/mo): unlimited checks, custom rules
- Team ($99/mo): CI/CD integrations, team dashboard

## License

MIT
