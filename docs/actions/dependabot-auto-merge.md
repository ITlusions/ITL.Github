# Dependabot Auto-Merge Action

Reusable composite action to automatically enable auto-merge on Dependabot PRs based on update type.

## Usage

```yaml
- uses: ITlusions/ITL.Github/actions/dependabot-auto-merge@v0.2.0
  with:
    pr_number: ${{ github.event.pull_request.number }}
    pr_title: ${{ github.event.pull_request.title }}
    merge_strategy: squash
    auto_merge_types: patch
```

## Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `pr_number` | Yes | — | Pull request number |
| `pr_title` | Yes | — | Pull request title |
| `merge_strategy` | No | `squash` | Merge strategy: `squash`, `merge`, or `rebase` |
| `auto_merge_types` | No | `patch` | Comma-separated update types to auto-merge: `patch`, `minor`, `major` |

## Outputs

| Output | Description |
|--------|-------------|
| `auto_merged` | Boolean: whether auto-merge was enabled |
| `merge_reason` | Reason for the merge decision |

## Examples

### Auto-merge patches only (default - safest)
```yaml
- uses: ITlusions/ITL.Github/actions/dependabot-auto-merge@v0.2.0
  with:
    pr_number: ${{ github.event.pull_request.number }}
    pr_title: ${{ github.event.pull_request.title }}
```

### Auto-merge patches and minor updates
```yaml
- uses: ITlusions/ITL.Github/actions/dependabot-auto-merge@v0.2.0
  with:
    pr_number: ${{ github.event.pull_request.number }}
    pr_title: ${{ github.event.pull_request.title }}
    auto_merge_types: patch,minor
    merge_strategy: squash
```

### Auto-merge all updates with rebase strategy
```yaml
- uses: ITlusions/ITL.Github/actions/dependabot-auto-merge@v0.2.0
  with:
    pr_number: ${{ github.event.pull_request.number }}
    pr_title: ${{ github.event.pull_request.title }}
    auto_merge_types: patch,minor,major
    merge_strategy: rebase
```

## How It Works

1. **Detects update type** from PR title (e.g., "Bump actions/setup-python from v5.0.0 to v5.0.1 (patch)")
2. **Compares against allowed types** from `auto_merge_types` input
3. **Enables auto-merge** only if update type matches
4. **Outputs results** for logging and conditional workflows

## Workflow Context Example

```yaml
name: Dependabot Auto-Merge

on:
  pull_request:
    types: [ opened, synchronize, reopened ]

permissions:
  pull-requests: write
  contents: write

jobs:
  auto-merge:
    runs-on: ubuntu-latest
    if: github.actor == 'dependabot[bot]'
    steps:
      - uses: ITlusions/ITL.Github/actions/dependabot-auto-merge@v0.2.0
        with:
          pr_number: ${{ github.event.pull_request.number }}
          pr_title: ${{ github.event.pull_request.title }}
          auto_merge_types: patch
```

## Safety Notes

- **Requires CI passing**: GitHub won't merge until all required status checks pass
- **Patches only by default**: Initial configuration auto-merges patches only (lowest risk)
- **No breaking changes**: Patch updates follow semver and contain only bug fixes
- **Requires permissions**: Workflow needs `pull-requests: write` and `contents: write`

## Integration

Use this action in consumer repos by adding a workflow that triggers on Dependabot PRs:

```yaml
uses: ITlusions/ITL.Github/.github/workflows/_dependabot-auto-merge.yml@v0.2.0
```

Or use the action directly in your own workflow (as shown above).
