# ITL.Github

Central repository for reusable GitHub Actions workflows and composite actions
shared across all ITLusions repositories.

## Reusable Workflows

Reference via `uses: ITlusions/ITL.Github/.github/workflows/<name>.yml@main`

| Workflow | Description |
|---|---|
| `_reusable-ci-python.yml` | Lint (ruff) + tests + wheel build |
| `_reusable-publish-pypi.yml` | Publish wheel to PyPI via OIDC Trusted Publishing |
| `_reusable-docker-build.yml` | Docker image build + push to registry |
| `_reusable-release-gh.yml` | Create GitHub Release with assets |
| `_reusable-auto-tag.yml` | Semver patch auto-tag on main |

## Composite Actions

Reference via `uses: ITlusions/ITL.Github/actions/<name>@main`

| Action | Description |
|---|---|
| `setup-python-env` | Python setup + pip install from requirements.txt |
| `detect-release-type` | Detect stable vs pre-release (rc/beta/alpha) |

## Usage

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
