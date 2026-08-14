# ITL.Github

Central repository for reusable GitHub Actions workflows and composite actions
shared across all ITLusions repositories.

**Full documentation:** [docs/README.md](docs/README.md)

## Reusable Workflows

Reference via `uses: ITlusions/ITL.Github/.github/workflows/<name>.yml@main`

| Workflow | Description | Docs |
|---|---|---|
| `_reusable-detect-version.yml` | Determine semver version from branch/tags | [docs](docs/workflows/detect-version.md) |
| `_reusable-ci-python.yml` | Lint (ruff) + tests + wheel build | [docs](docs/workflows/ci-python.md) |
| `_reusable-ci-docker.yml` | Lint + test + Docker build/push | [docs](docs/workflows/ci-docker.md) |
| `_reusable-auto-tag.yml` | Semver patch auto-tag on main | [docs](docs/workflows/auto-tag.md) |
| `_reusable-docker-retag.yml` | Promote image by retagging (no rebuild) | [docs](docs/workflows/docker-retag.md) |
| `_reusable-publish-pypi.yml` | Publish wheel to PyPI via OIDC | [docs](docs/workflows/publish-pypi.md) |
| `_reusable-release-gh.yml` | Create GitHub Release with assets | [docs](docs/workflows/release-gh.md) |
| `_reusable-claude-plugin-validate.yml` | Validate a Claude Code plugin/marketplace manifest | [docs](docs/workflows/claude-plugin-validate.md) |
| `_reusable-claude-plugin-version-tag.yml` | Subdirectory-scoped semver + tag for one plugin in a multi-plugin repo | [docs](docs/workflows/claude-plugin-version-tag.md) |
| `_reusable-claude-plugin-release.yml` | Publish a GitHub Release for one Claude Code plugin | [docs](docs/workflows/claude-plugin-release.md) |
| `_reusable-claude-plugin-publish.yml` | Version + tag + release one plugin as a single `publish` job | [docs](docs/workflows/claude-plugin-publish.md) |

## Composite Actions

Reference via `uses: ITlusions/ITL.Github/actions/<name>@main`

| Action | Description | Docs |
|---|---|---|
| `setup-python-env` | Python setup + pip install from requirements.txt | [docs](docs/actions/setup-python-env.md) |
| `detect-release-type` | Detect stable vs pre-release (rc/beta/alpha) | [docs](docs/actions/detect-release-type.md) |

## Quick Start

```yaml
# Reusable workflow
jobs:
  ci:
    uses: ITlusions/ITL.Github/.github/workflows/_reusable-ci-python.yml@main
    with:
      python-version: "3.12"
      artifact-name: "myproject-wheel"

# Composite action
steps:
  - uses: ITlusions/ITL.Github/actions/setup-python-env@main
    with:
      python-version: "3.12"
```

See [Getting Started](docs/getting-started.md) for a full walkthrough.
