# Composite Actions

All actions live in `actions/` and are called via:

```yaml
steps:
  - uses: ITlusions/ITL.Github/actions/<name>@main
```

## Overview

| Action | Directory | Purpose |
|---|---|---|
| [Setup Python Env](setup-python-env.md) | `actions/setup-python-env` | Python setup, pip cache, dependency install |
| [Detect Release Type](detect-release-type.md) | `actions/detect-release-type` | Determine stable vs pre-release from version string |

## Composite vs Reusable Workflow

| | Composite Action | Reusable Workflow |
|---|---|---|
| Used in | `steps:` | `jobs:` |
| Runs in | Same job | Separate job |
| Can define services | No | Yes |
| Overhead | Minimal | One job spin-up |

Use composite actions for small, reusable step sequences.
Use reusable workflows when you need services (PostgreSQL, Redis) or parallelism.
