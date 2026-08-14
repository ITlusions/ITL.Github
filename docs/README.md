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
| **NEW:** [`_reusable-python-ci.yml`](workflows/reusable-python-ci.md) | Test + lint + build Python wheels (setuptools-scm) |
| **NEW:** [`_reusable-python-publish.yml`](workflows/reusable-python-publish.md) | Smart PyPI/TestPyPI publishing (branch-aware + OIDC + SBOM + attestation) |
| [`_reusable-detect-version.yml`](workflows/detect-version.md) | Determine semver version from branch/tags |
| [`_reusable-ci-python.yml`](workflows/ci-python.md) | Lint + test + wheel build (Python) |
| [`_reusable-ci-docker.yml`](workflows/ci-docker.md) | Lint + test + Docker build/push |
| [`_reusable-auto-tag.yml`](workflows/auto-tag.md) | Push semver patch tag on main |
| [`_reusable-docker-retag.yml`](workflows/docker-retag.md) | Promote image by retagging (no rebuild) |
| [`_reusable-publish-pypi.yml`](workflows/publish-pypi.md) | Publish wheel to PyPI via OIDC |
| [`_reusable-release-gh.yml`](workflows/release-gh.md) | Create GitHub Release with assets |
| [`_reusable-claude-plugins-ci.yml`](workflows/claude-plugins-ci.md) | Validate a Claude Code plugin/marketplace manifest |
| [`_reusable-claude-plugin-version-tag.yml`](workflows/claude-plugin-version-tag.md) | Subdirectory-scoped semver + tag for one plugin in a multi-plugin repo |
| [`_reusable-claude-plugin-release.yml`](workflows/claude-plugin-release.md) | Publish a GitHub Release for one Claude Code plugin |
| [`_reusable-claude-plugins-publish.yml`](workflows/claude-plugins-publish.md) | Version + tag + release one plugin as a single `publish` job |

### Composite Actions

```
uses: ITlusions/ITL.Github/actions/<name>@main
```

| Directory | Purpose |
|---|---|
| [`python-publish`](actions/python-publish.md) | Build, SBOM, attest, publish Python packages (OIDC-compatible) |
| [`dependabot-auto-merge`](actions/dependabot-auto-merge.md) | Auto-merge Dependabot PRs by update type |
| [`setup-python-env`](actions/setup-python-env.md) | Python setup + pip install |
| [`detect-release-type`](actions/detect-release-type.md) | Stable vs pre-release detection |
