# CI — Docker

**File:** `_reusable-ci-docker.yml`

Runs lint (ruff), tests (pytest), and validates a Docker build. Optionally pushes the image
to a container registry. Supports multi-repo checkout for projects where the Dockerfile
depends on a sibling library repository.

## Checkout Layout

When `dependency-repo` is set, the runner workspace looks like:

```
$GITHUB_WORKSPACE/
├── <checkout-path>/       ← this repo (e.g. ITL.BrainCell.Api)
└── <dependency-path>/     ← dependency repo (e.g. ITL.BrainCell)
```

The Docker build context is the parent directory containing both.

## Steps

1. Checkout main repo into `checkout-path`
2. Checkout `dependency-repo` into `dependency-path` (if set)
3. Setup Python + install dependencies (installs dependency as editable package)
4. Lint with ruff
5. Run pytest
6. Set up Docker Buildx
7. Log in to registry (only if `push: true`)
8. Resolve image tag (`version` input or `ci-<sha>` fallback)
9. Build Docker image (+ push if `push: true`)

## Inputs

| Input | Type | Default | Description |
|---|---|---|---|
| `image-name` | string | **required** | Full image name, e.g. `ghcr.io/itlusions/myapp` |
| `python-version` | string | `3.12` | Python version |
| `ref` | string | `""` | Git ref for this repo |
| `checkout-path` | string | `app` | Directory to check out this repo into |
| `ruff-src` | string | `src/` | Directory ruff scans (relative to `checkout-path`) |
| `test-path` | string | `tests/` | Directory pytest scans (relative to `checkout-path`) |
| `dockerfile` | string | `Dockerfile` | Path to Dockerfile (relative to `checkout-path`) |
| `dependency-repo` | string | `""` | Optional dependency repo, e.g. `ITlusions/ITL.BrainCell` |
| `dependency-ref` | string | `main` | Ref for the dependency repo |
| `dependency-path` | string | `dependency` | Directory to check out the dependency into |
| `version` | string | `""` | Docker image tag. Empty = `ci-<sha>` |
| `push` | boolean | `false` | Push the built image to the registry |
| `registry` | string | `ghcr.io` | Container registry URL |
| `registry-username` | string | `""` | Registry username (defaults to `github.actor`) |

## Secrets

| Secret | Required | Description |
|---|---|---|
| `gh-pat` | When `push: true` or `dependency-repo` set | PAT for cross-repo checkout and registry push |

## Outputs

| Output | Description |
|---|---|
| `image-tag` | Full image reference that was built/pushed (`image:version`) |
| `image-digest` | Docker image digest from the build |

## Usage

```yaml
jobs:
  detect-version:
    uses: ITlusions/ITL.Github/.github/workflows/_reusable-detect-version.yml@main

  ci:
    needs: detect-version
    uses: ITlusions/ITL.Github/.github/workflows/_reusable-ci-docker.yml@main
    with:
      image-name: "ghcr.io/itlusions/braincell-api"
      checkout-path: "ITL.BrainCell.Api"
      dependency-repo: "ITlusions/ITL.BrainCell"
      dependency-path: "ITL.BrainCell"
      version: ${{ needs.detect-version.outputs.image-tag }}
      push: ${{ github.event_name == 'push' && github.ref == 'refs/heads/main' }}
      registry-username: ${{ github.actor }}
    secrets:
      gh-pat: ${{ secrets.GH_PAT }}
```

## Notes

- When `push: false` (default), the image is built and validated but not pushed.
  Use this on feature branches and PRs.
- The image tag resolves to `ci-<sha>` when no `version` is provided.
  Always pass `detect-version.outputs.image-tag` for consistent tagging.
- The built image tag is available as `needs.ci.outputs.image-tag` for downstream retag jobs.
