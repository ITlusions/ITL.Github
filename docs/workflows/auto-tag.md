# Auto-tag

**File:** `_reusable-auto-tag.yml`

Reads the highest existing semver tag in the repository and pushes a patch bump tag
to the specified commit. Used at the end of a successful CI run on `main` or `release/**`.

## Version Bumping

| Current highest tag | New tag |
|---|---|
| `v0.1.2` | `v0.1.3` |
| `v1.4.9` | `v1.4.10` |
| *(no tags)* | `v0.1.0` (from `initial-version`) |

Only the **patch** component is incremented. Major and minor bumps must be done manually.

## Inputs

| Input | Type | Default | Description |
|---|---|---|---|
| `commit-sha` | string | `""` | Commit SHA to tag. Empty = HEAD of default branch |
| `tag-prefix` | string | `v` | Prefix for the tag, e.g. `v` |
| `initial-version` | string | `0.1.0` | Version to use when no tags exist yet |

## Secrets

| Secret | Required | Description |
|---|---|---|
| `gh-pat` | Recommended | PAT for pushing the tag. Required if `GITHUB_TOKEN` lacks `contents: write` |

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
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    uses: ITlusions/ITL.Github/.github/workflows/_reusable-auto-tag.yml@main
    with:
      commit-sha: ${{ github.sha }}
    secrets:
      gh-pat: ${{ secrets.GH_PAT }}
```

## Notes

- Tags pushed via a PAT do **not** trigger other GitHub Actions workflows.
  This is a GitHub security restriction. Use `on-push.yml` to chain all jobs
  in a single workflow file instead of relying on tag-triggered workflows.
- The `tag` output can be passed to [`_reusable-release-gh.yml`](release-gh.md)
  and [`_reusable-docker-retag.yml`](docker-retag.md).
- Always guard this job with `if: github.ref == 'refs/heads/main'` (or `release/**`)
  to prevent tagging feature branches.
