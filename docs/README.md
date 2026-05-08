# ITL.Github — Documentation

Central repository for reusable GitHub Actions workflows and composite actions
shared across all ITLusions repositories.

## Navigation

| Section | Description |
|---|---|
| [Getting Started](getting-started.md) | How to consume workflows and actions from another repo |
| [Versioning](versioning.md) | `@main` vs pinned refs, update strategy |
| [Workflows](workflows/README.md) | Reference for all reusable workflows |
| [Actions](actions/README.md) | Reference for all composite actions |
| [Guide: Python Library](guides/python-library.md) | Full CI/CD pipeline for a Python package |
| [Guide: Docker Service](guides/docker-service.md) | Full CI/CD pipeline for a Docker-based service |

## Quick Reference

### Reusable Workflows

```
uses: ITlusions/ITL.Github/.github/workflows/<name>.yml@main
```

| File | Purpose |
|---|---|
| [`_reusable-detect-version.yml`](workflows/detect-version.md) | Determine semver version from branch/tags |
| [`_reusable-ci-python.yml`](workflows/ci-python.md) | Lint + test + wheel build (Python) |
| [`_reusable-ci-docker.yml`](workflows/ci-docker.md) | Lint + test + Docker build/push |
| [`_reusable-auto-tag.yml`](workflows/auto-tag.md) | Push semver patch tag on main |
| [`_reusable-docker-retag.yml`](workflows/docker-retag.md) | Promote image by retagging (no rebuild) |
| [`_reusable-publish-pypi.yml`](workflows/publish-pypi.md) | Publish wheel to PyPI via OIDC |
| [`_reusable-release-gh.yml`](workflows/release-gh.md) | Create GitHub Release with assets |

### Composite Actions

```
uses: ITlusions/ITL.Github/actions/<name>@main
```

| Directory | Purpose |
|---|---|
| [`setup-python-env`](actions/setup-python-env.md) | Python setup + pip install |
| [`detect-release-type`](actions/detect-release-type.md) | Stable vs pre-release detection |
