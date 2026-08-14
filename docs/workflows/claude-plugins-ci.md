# Claude Plugins CI

**File:** `_reusable-claude-plugins-ci.yml`

Validates a Claude Code plugin or marketplace manifest via `claude plugin validate --strict`.
Installs `@anthropic-ai/claude-code` and runs the validator against a given path — either a
single plugin directory (checks its `.claude-plugin/plugin.json`) or a marketplace root (checks
`.claude-plugin/marketplace.json`).

## Inputs

| Input | Type | Default | Description |
|---|---|---|---|
| `path` | string | *(required)* | Path to a plugin directory, or `.` for a marketplace root |
| `claude-code-version` | string | `latest` | npm version spec for `@anthropic-ai/claude-code` |

## Usage

```yaml
jobs:
  validate-marketplace:
    uses: ITlusions/ITL.Github/.github/workflows/_reusable-claude-plugins-ci.yml@main
    with:
      path: "."

  validate-plugin:
    uses: ITlusions/ITL.Github/.github/workflows/_reusable-claude-plugins-ci.yml@main
    with:
      path: "plugins/my-plugin"
```

For a repo with multiple plugins, call this once per plugin via a matrix — see
[claude-plugin-version-tag.md](claude-plugin-version-tag.md) for the full multi-plugin pattern.
