# Publish PyPI

**File:** `_reusable-publish-pypi.yml`

Publishes a Python wheel to PyPI or TestPyPI using OIDC Trusted Publishing.
No API tokens or secrets are required — authentication is handled via GitHub's OIDC provider.

## How It Works

1. Finds the successful CI run that built the wheel for the given commit SHA.
2. Downloads the wheel artifact from that run.
3. Publishes via `twine upload` with OIDC credentials.

The wheel is **never rebuilt** — the artifact from CI is the only source.

## OIDC Trusted Publisher Setup

Before this workflow can publish, a Trusted Publisher must be configured on PyPI:

| Field | Value |
|---|---|
| Owner | `ITlusions` |
| Repository | Your repo name (e.g. `ITL.Braincell`) |
| Workflow file name | `publish.yml` |
| Environment name | `production` (stable) or `staging` (pre-release) |

See [PyPI Trusted Publishers docs](https://docs.pypi.org/trusted-publishers/) for setup instructions.

## Tag Routing

| Tag format | Target | GitHub Environment |
|---|---|---|
| `v1.2.3` (no suffix) | PyPI (production) | `production` |
| `v1.2.3-rc.N` | TestPyPI | `staging` |
| `v1.2.3-beta.N` | TestPyPI | `staging` |
| `v1.2.3-alpha.N` | TestPyPI | `staging` |

## Inputs

| Input | Type | Default | Description |
|---|---|---|---|
| `artifact-name` | string | `python-wheel` | Name of the wheel artifact uploaded by CI |
| `ci-workflow-name` | string | `CI — Branch push` | Name of the CI workflow to search for the artifact |
| `commit-sha` | string | **required** | Commit SHA to find the CI artifact for |
| `environment` | string | `production` | GitHub environment name (controls PyPI vs TestPyPI) |
| `python-version` | string | `3.12` | Python version for twine |
| `fallback-build` | boolean | `true` | Build wheel from source if artifact is not found |
| `working-directory` | string | `.` | Working directory for fallback build |

## Outputs

| Output | Description |
|---|---|
| `published` | `"true"` if the wheel was successfully published |
| `ci-run-id` | Run ID of the CI workflow the artifact was downloaded from |

## Required Permissions

The calling job must declare:

```yaml
permissions:
  contents: read
  actions: read
  id-token: write   # required for OIDC
```

## Usage

```yaml
on:
  release:
    types: [published]

jobs:
  publish:
    uses: ITlusions/ITL.Github/.github/workflows/_reusable-publish-pypi.yml@main
    with:
      artifact-name: "myproject-wheel"
      commit-sha: ${{ github.event.release.target_commitish }}
      ci-workflow-name: "CI — Build & Test"
      environment: "production"
      fallback-build: false
```

## Notes

- Set `fallback-build: false` in production pipelines to enforce the build-once contract.
- The `environment` value must match the GitHub Environment name configured in your repo
  settings and on PyPI's Trusted Publisher configuration.
- The workflow uses `gh run list --commit <sha>` to find the CI artifact.
  This requires `actions: read` permission.
