# Reusable Workflows

All workflows live in `.github/workflows/` and are called via:

```yaml
uses: ITlusions/ITL.Github/.github/workflows/<filename>@main
```

## Overview

| Workflow | File | Purpose |
|---|---|---|
| [Detect Version](detect-version.md) | `_reusable-detect-version.yml` | Determine a semver version from branch name and git tags |
| [CI — Python](ci-python.md) | `_reusable-ci-python.yml` | Lint (ruff) + test (pytest + PostgreSQL) + wheel build |
| [CI — Docker](ci-docker.md) | `_reusable-ci-docker.yml` | Lint + test + Docker build (+ optional push) |
| [Auto-tag](auto-tag.md) | `_reusable-auto-tag.yml` | Push a semver patch bump tag to the repo |
| [Docker Retag](docker-retag.md) | `_reusable-docker-retag.yml` | Promote an image by retagging without rebuilding |
| [Publish PyPI](publish-pypi.md) | `_reusable-publish-pypi.yml` | Publish a wheel to PyPI or TestPyPI via OIDC |
| [GitHub Release](release-gh.md) | `_reusable-release-gh.yml` | Create a GitHub Release with optional artifact assets |

## Typical Job Order

For a Python library:
```
detect-version → ci-python → auto-tag → release-gh
                                              ↓ (release: published)
                                         publish-pypi
```

For a Docker service:
```
detect-version → ci-docker (build+push) → auto-tag → docker-retag → release-gh
```
