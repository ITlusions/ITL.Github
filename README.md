# ITL.Github

Central repository for reusable GitHub Actions workflows and composite actions
shared across all ITLusions repositories.

**Full documentation:** [docs/README.md](docs/README.md)

## Reusable Workflows

Reference via `uses: ITlusions/ITL.Github/.github/workflows/<name>.yml@main`

| Workflow | Description | Docs |
|---|---|---|
| `_managed-detect-version.yml` | Determine semver version from branch/tags | [source](.github/workflows/_managed-detect-version.yml) |
| `_managed-ci-python.yml` | Lint (ruff) + tests + wheel build | [source](.github/workflows/_managed-ci-python.yml) |
| `_managed-ci-docker.yml` | Lint + test + Docker build/push | [source](.github/workflows/_managed-ci-docker.yml) |
| `_managed-auto-tag.yml` | Semver patch auto-tag on main | [source](.github/workflows/_managed-auto-tag.yml) |
| `_managed-docker-retag.yml` | Promote image by retagging (no rebuild) | [source](.github/workflows/_managed-docker-retag.yml) |
| `_managed-publish-pypi.yml` | Publish wheel to PyPI via OIDC | [source](.github/workflows/_managed-publish-pypi.yml) |
| `_managed-release-gh.yml` | Create GitHub Release with assets | [source](.github/workflows/_managed-release-gh.yml) |
| `_managed-claude-plugins-ci.yml` | Validate a Claude Code plugin/marketplace manifest | [source](.github/workflows/_managed-claude-plugins-ci.yml) |
| `_managed-claude-plugin-version-tag.yml` | Subdirectory-scoped semver + tag for one plugin in a multi-plugin repo | [source](.github/workflows/_managed-claude-plugin-version-tag.yml) |
| `_managed-claude-plugin-release.yml` | Publish a GitHub Release for one Claude Code plugin | [source](.github/workflows/_managed-claude-plugin-release.yml) |
| `_managed-claude-plugins-publish.yml` | Version + tag + release one plugin as a single `publish` job | [source](.github/workflows/_managed-claude-plugins-publish.yml) |

## Composite Actions

Reference via `uses: ITlusions/ITL.Github/actions/<name>@main`

| Action | Description | Docs |
|---|---|---|
| `setup-python-env` | Python setup + pip install from requirements.txt | [source](actions/setup-python-env/action.yml) |
| `detect-release-type` | Detect stable vs pre-release (rc/beta/alpha) | [source](actions/detect-release-type/action.yml) |

## Quick Start

```yaml
# Reusable workflow
jobs:
  ci:
    uses: ITlusions/ITL.Github/.github/workflows/_managed-ci-python.yml@main
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
