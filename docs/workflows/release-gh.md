# GitHub Release

**File:** `_reusable-release-gh.yml`

Creates a GitHub Release for a given tag, optionally attaching a build artifact
(e.g. a wheel file) as a release asset.

## Release Type Detection

The workflow automatically determines whether the release is stable or a pre-release
based on the tag name:

| Tag | Type |
|---|---|
| `v1.2.3` | Stable release |
| `v1.2.3-rc.1` | Pre-release |
| `v1.2.3-beta.2` | Pre-release |
| `v1.2.3-alpha.1` | Pre-release |

## Steps

1. Detect release type from tag name
2. Download artifact (if `artifact-name` is set)
3. Create GitHub Release via `softprops/action-gh-release`
4. Attach artifact as release asset (if downloaded successfully)

## Inputs

| Input | Type | Default | Description |
|---|---|---|---|
| `tag` | string | **required** | Release tag, e.g. `v1.2.3` |
| `artifact-name` | string | `""` | Name of the artifact to attach as a release asset. Empty = no asset |
| `artifact-run-id` | string | `""` | Run ID of the workflow that produced the artifact. Empty = current run |
| `generate-release-notes` | boolean | `true` | Auto-generate release notes from commit history |
| `body` | string | `""` | Optional release body text (Markdown) |

## Outputs

| Output | Description |
|---|---|
| `release-url` | URL of the created GitHub Release |

## Required Permissions

```yaml
permissions:
  contents: write   # required to create releases
  actions: read     # required to download artifacts from other runs
```

## Usage

```yaml
jobs:
  create-release:
    needs: auto-tag
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    uses: ITlusions/ITL.Github/.github/workflows/_reusable-release-gh.yml@main
    with:
      tag: ${{ needs.auto-tag.outputs.tag }}
      artifact-name: "myproject-wheel"
      generate-release-notes: true
```

## Notes

- If `artifact-name` is set but the artifact is not found, the step uses
  `continue-on-error: true` — the release is still created without the asset.
- Creating a release with `draft: false` and `prerelease: false` (stable) fires
  the `release: published` event, which can trigger a downstream `publish.yml`.
- When passing an artifact from a different run (e.g. from a CI run earlier in the pipeline),
  set `artifact-run-id` to the CI run's ID.
