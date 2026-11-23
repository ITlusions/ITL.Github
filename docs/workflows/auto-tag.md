# Auto-tag

**File:** `_managed-auto-tag.yml`

Computes the version from the latest GitHub release and the `baseversion` floor. It does not push a tag:
the tag is created by the GitHub release that follows. Used for `main` (patch bump) and, with `prerelease: true`,
for other branches (branch prerelease tag, no bump).

## Version Source

The version is taken from the latest published release (pre-releases and drafts are ignored).
The `baseversion` in the metadata file (default `.metadata.json`) is the floor:

- No release exists: the tag is `baseversion`.
- `baseversion` is higher than the latest release: the tag is `baseversion`.
- Otherwise: the patch of the latest release is incremented.

## Version Bumping

| Latest release | `baseversion` | New tag |
|---|---|---|
| `v0.2.18` | `0.2.18` | `v0.2.19` |
| `v0.2.18` | `1.0.0` | `v1.0.0` |
| *(none)* | `0.2.18` | `v0.2.18` |

Only the **patch** component is incremented. Major and minor bumps are done by raising `baseversion`.

## Inputs

| Input | Type | Default | Description |
|---|---|---|---|
| `prerelease` | boolean | `false` | Branch build: no patch bump, appends `-<branch>.<run>+<sha7>` |
| `tag-prefix` | string | `v` | Prefix for the tag, e.g. `v` |
| `metadata-file` | string | `.metadata.json` | JSON file with a `baseversion` (`X.Y.Z`) used as the floor. Defaults to `0.1.0` if the file is absent |

## Outputs

| Output | Description | Example |
|---|---|---|
| `tag` | Created tag | `v0.1.3` |
| `version` | Version without prefix | `0.1.3` |

## Usage

```yaml
jobs:
  auto-tag:
    needs: ci
    if: github.event_name == 'push'
    uses: ITlusions/ITL.Github/.github/workflows/_managed-auto-tag.yml@main
    with:
      prerelease: ${{ github.ref != 'refs/heads/main' }}
```

## Notes

- Tags pushed via a PAT do **not** trigger other GitHub Actions workflows.
  This is a GitHub security restriction. Use `on-push.yml` to chain all jobs
  in a single workflow file instead of relying on tag-triggered workflows.
- The `tag` output can be passed to [`_managed-release-gh.yml`](release-gh.md)
  and [`_managed-docker-retag.yml`](docker-retag.md).
- Always guard this job with `if: github.ref == 'refs/heads/main'` (or `release/**`)
  to prevent tagging feature branches.
