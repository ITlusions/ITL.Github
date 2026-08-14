# Claude Plugin Release

**File:** `_reusable-claude-plugin-release.yml`

Publishes a GitHub Release for one Claude Code plugin. Resolves the plugin's *current* version
directly from its `plugin.json` (no need to pass a version in), skips (idempotently) if a release
for that `{component-name}--v{version}` tag already exists, otherwise re-validates the plugin,
zips it, and delegates actual release creation to
[`_reusable-release-gh.yml`](release-gh.md) (a nested reusable-workflow call within this same
repo).

Because it re-derives the tag from `plugin.json` and is a no-op when the release already exists,
it's safe to call on **every plugin, on every push** — you don't need to track which plugins were
just tagged.

## Inputs

| Input | Type | Default | Description |
|---|---|---|---|
| `component-path` | string | *(required)* | Path to the plugin directory (contains `.claude-plugin/plugin.json`) |
| `component-name` | string | *(required)* | Plugin name, used as the tag prefix: `{component-name}--v{version}` |
| `ref` | string | *(event ref)* | Branch/tag/SHA to check out. **Pass this when chaining right after a job that just committed a version bump** (e.g. `_reusable-claude-plugin-version-tag.yml`'s `tag` output) — without it, this job's own checkout resolves the original triggering ref, not the fresh commit, and reads the plugin's previous (already-released) version instead of the one just tagged |
| `claude-code-version` | string | `latest` | npm version spec for `@anthropic-ai/claude-code` |

## Outputs

| Output | Description |
|---|---|
| `release-url` | URL of the created (or pre-existing) GitHub Release |

## Usage

```yaml
jobs:
  release:
    needs: discover
    strategy:
      matrix:
        plugin: ${{ fromJson(needs.discover.outputs.plugins) }}
    uses: ITlusions/ITL.Github/.github/workflows/_reusable-claude-plugin-release.yml@main
    with:
      component-path: plugins/${{ matrix.plugin }}
      component-name: ${{ matrix.plugin }}
    permissions:
      contents: write
      actions: read
```

Pair with [claude-plugin-version-tag.md](claude-plugin-version-tag.md), which produces the tag
this workflow releases, and [claude-plugins-ci.md](claude-plugins-ci.md) for the
validation step run before either.

Release zip URLs (`.../releases/download/{tag}/{name}-{version}.zip`) are usable directly with
`claude --plugin-url <url>` for one-off session loads.
