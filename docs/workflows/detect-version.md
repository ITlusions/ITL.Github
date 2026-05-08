# Detect Version

**File:** `_reusable-detect-version.yml`

Determines a semver-based version string from the current branch and git tags.
Outputs both a raw semver version and format-specific variants for Docker and Python wheels.

## Version Scheme

| Branch | Output (`version`) | Example |
|---|---|---|
| `main` | Next patch bump | `0.1.3` |
| `release/**` | Current + rc suffix | `0.1.3-rc.1` |
| `feature/**`, `develop`, `hotfix/**` | Current + branch slug + run | `0.1.2-feature-login.42-abc1234` |

The current version is determined by the highest existing `v*` tag in the repository.
If no tags exist, `initial-version` is used as the base.

## Inputs

| Input | Type | Default | Description |
|---|---|---|---|
| `tag-prefix` | string | `v` | Prefix used on git tags |
| `initial-version` | string | `0.1.0` | Starting version when no tags exist |

## Outputs

| Output | Description | Example |
|---|---|---|
| `version` | Full semver string | `0.1.3` / `0.1.2-feature-login.42+abc1234` |
| `image-tag` | Docker-safe version (no `+`) | `0.1.3` / `0.1.2-feature-login.42-abc1234` |
| `python-version` | PEP 440 version for Python wheel | `0.1.3` / `0.1.2.dev42+abc1234` |
| `tag` | Prefixed tag for main builds | `v0.1.3` / `""` (empty on non-main) |
| `is-release` | `"true"` only on main | `"true"` / `"false"` |

## Usage

```yaml
jobs:
  detect-version:
    uses: ITlusions/ITL.Github/.github/workflows/_reusable-detect-version.yml@main

  ci:
    needs: detect-version
    uses: ITlusions/ITL.Github/.github/workflows/_reusable-ci-python.yml@main
    with:
      version: ${{ needs.detect-version.outputs.python-version }}
```

## Notes

- `image-tag` replaces `+` with `-` to comply with Docker tag character restrictions.
- `python-version` uses `.devN+sha` format (PEP 440) for pre-release wheels.
- On `main`, `is-release: "true"` — use this to gate push/tag/release jobs.
