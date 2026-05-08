# Docker Retag

**File:** `_reusable-docker-retag.yml`

Promotes an existing Docker image to a new tag by retagging it — no rebuild, no new layer.
Uses `docker buildx imagetools create` which is a manifest-only operation.

## Why Retag Instead of Rebuild?

Rebuilding from source produces a technically different image (different digest, possible
environment drift). Retagging guarantees that the image tested in CI is identical to the
image released in production. This is the recommended promotion pattern.

```
CI build:      ghcr.io/org/app:0.1.4-feature-x.12-abc1234
                         ↓  retag (no rebuild)
Release tag:   ghcr.io/org/app:v0.1.4
```

## Inputs

| Input | Type | Default | Description |
|---|---|---|---|
| `source-image` | string | **required** | Full source image with tag, e.g. `ghcr.io/itlusions/app:0.1.3-ci` |
| `target-image` | string | **required** | Target image name without tag, e.g. `ghcr.io/itlusions/app` |
| `target-tag` | string | **required** | New tag to apply, e.g. `v0.1.3` or `latest` |
| `registry` | string | `ghcr.io` | Container registry URL |
| `registry-username` | string | `""` | Registry username (defaults to `github.actor`) |

## Secrets

| Secret | Required | Description |
|---|---|---|
| `registry-password` | Yes | Registry password or token (e.g. `GH_PAT` for GHCR) |

## Outputs

| Output | Description | Example |
|---|---|---|
| `image-ref` | Full image reference after retag | `ghcr.io/itlusions/app:v0.1.3` |

## Usage

```yaml
jobs:
  docker:
    needs: [ci, auto-tag]
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    uses: ITlusions/ITL.Github/.github/workflows/_reusable-docker-retag.yml@main
    with:
      source-image: ${{ needs.ci.outputs.image-tag }}
      target-image: "ghcr.io/itlusions/braincell-api"
      target-tag: ${{ needs.auto-tag.outputs.tag }}
    secrets:
      registry-password: ${{ secrets.GH_PAT }}
```

## Notes

- The `source-image` must have been pushed before this job runs.
  Ensure `push: true` is set in the CI job on `main` builds.
- `docker buildx imagetools create` does not pull layers — it only copies the manifest.
  This operation is fast and registry-side only.
- You can apply multiple tags by calling this workflow multiple times
  (e.g. once for `v0.1.3`, once for `latest`).
