# Claude Plugins Publish

**File:** `_reusable-claude-plugins-publish.yml`

Version, tag, and release one Claude Code plugin as a single callable unit — chains
[`_reusable-claude-plugin-version-tag.yml`](claude-plugin-version-tag.md) and
[`_reusable-claude-plugin-release.yml`](claude-plugin-release.md) (nested reusable-workflow
calls) so a caller pipeline can have one `publish` job instead of two, matching the
`ci` + `publish` shape used across ITLusions pipelines (see
[`_reusable-python-publish.yml`](reusable-python-publish.md) for the Python equivalent).

Idempotent end to end: no-ops the tag if the plugin's directory hasn't changed since its last
tag, and no-ops the release if one already exists for the current tag. Safe to call on every push
to the target branch.

## Inputs

| Input | Type | Default | Description |
|---|---|---|---|
| `component-path` | string | *(required)* | Path to the plugin directory (contains `.claude-plugin/plugin.json`) |
| `component-name` | string | *(required)* | Plugin name, used as the tag prefix: `{component-name}/v{version}` |
| `branch` | string | `main` | Branch to commit the version bump and tag on |
| `claude-code-version` | string | `latest` | npm version spec for `@anthropic-ai/claude-code` |

## Secrets

| Secret | Required | Description |
|---|---|---|
| `gh-pat` | Optional | PAT for pushing the version bump/tag. Falls back to `GITHUB_TOKEN` |

## Outputs

| Output | Description |
|---|---|
| `changed` | `'true'` if a new version was computed and tagged |
| `version` | Resolved version, e.g. `1.0.2` |
| `tag` | Tag name, e.g. `my-plugin/v1.0.2` |
| `release-url` | URL of the created (or pre-existing) GitHub Release |

## Usage

Mirrors the `ci` + `publish` shape used elsewhere in ITLusions pipelines (e.g.
`ITL.Braincell.SDK`'s `pipeline.yml`). For multiple plugins in one repo, add a matrix — `ci`
matrix-validates each, `publish` matrix-publishes each (`max-parallel: 1`, since each call
commits + pushes to `branch`):

```yaml
name: Pipeline

on:
  pull_request:
    branches: [ master ]
  push:
    branches: [ master, 'feature/**', 'hotfix/**' ]
  workflow_dispatch:

jobs:
  ci:
    strategy:
      matrix:
        plugin: [ my-plugin ]   # add another entry per additional plugin
    uses: ITlusions/ITL.Github/.github/workflows/_reusable-claude-plugins-ci.yml@main
    with:
      path: plugins/${{ matrix.plugin }}

  publish:
    needs: [ ci ]
    if: github.ref == 'refs/heads/master'
    strategy:
      max-parallel: 1
      matrix:
        plugin: [ my-plugin ]
    uses: ITlusions/ITL.Github/.github/workflows/_reusable-claude-plugins-publish.yml@main
    with:
      component-path: plugins/${{ matrix.plugin }}
      component-name: ${{ matrix.plugin }}
      branch: master
    permissions:
      contents: write
      actions: read
```
