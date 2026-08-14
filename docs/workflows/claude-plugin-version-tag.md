# Claude Plugin Version + Tag

**File:** `_reusable-claude-plugin-version-tag.yml`

Computes the next semver for one Claude Code plugin living in its own subdirectory (of a
possibly multi-plugin marketplace repo), based on conventional-commit messages touching that
subdirectory since its last `{component-name}/v{version}` tag. Writes the version into
`plugin.json`, commits, and tags via `claude plugin tag` (which also validates that `plugin.json`
and any enclosing `marketplace.json` entry agree).

Unlike [`_reusable-auto-tag.yml`](auto-tag.md), this is scoped to one component's subdirectory
and reads conventional-commit prefixes to size the bump, rather than always patch-bumping the
whole repo — needed for a repo containing several independently-versioned plugins.

## Idempotency

No-ops (`changed=false`) if nothing under `component-path` changed since the plugin's last tag.
A plugin with no tag yet keeps whatever version is currently committed in `plugin.json` as its v1
baseline — nothing is auto-bumped on the very first run, and no commit is made (the baseline
version is already correct as committed by whoever added the plugin), only a tag. Safe to call on
every push.

## Version Bumping

| Conventional-commit prefix touching `component-path` since the last tag | Bump |
|---|---|
| `feat!: ...` or a `BREAKING CHANGE` footer | major |
| `feat: ...` / `feat(scope): ...` | minor |
| anything else (`fix:`, `chore:`, `docs:`, ...) | patch |

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
| `gh-pat` | Optional | PAT for pushing. Falls back to `GITHUB_TOKEN` |

## Outputs

| Output | Description | Example |
|---|---|---|
| `changed` | `'true'` if a new version was tagged | `true` |
| `version` | Resolved version | `1.0.2` |
| `tag` | Tag name | `my-plugin/v1.0.2` |

## Usage

Multi-plugin marketplace repo, called via a matrix discovered at runtime. Use
`max-parallel: 1` — each call commits and pushes to `branch`, and parallel matrix jobs pushing
to the same branch will race:

```yaml
jobs:
  version-and-tag:
    if: github.ref == 'refs/heads/main'
    strategy:
      max-parallel: 1
      matrix:
        plugin: ${{ fromJson(needs.discover.outputs.plugins) }}
    uses: ITlusions/ITL.Github/.github/workflows/_reusable-claude-plugin-version-tag.yml@main
    with:
      component-path: plugins/${{ matrix.plugin }}
      component-name: ${{ matrix.plugin }}
      branch: main
    permissions:
      contents: write
```

Pair with [claude-plugin-release.md](claude-plugin-release.md) to publish a GitHub Release once
tagged.
