# Versioning

## Using `@main`

All workflows and actions in this repo are referenced with `@main`:

```yaml
uses: ITlusions/ITL.Github/.github/workflows/_reusable-ci-python.yml@main
```

**This is the recommended approach** for all ITLusions repositories because:
- Changes to shared workflows take effect immediately across all consumers.
- Fixes and improvements propagate automatically.
- There is a single source of truth.

The tradeoff is that breaking changes in this repo can affect all consumers at once.
Any breaking change must therefore be tested carefully before merging to `main`.

## Pinning to a SHA

If you need stability guarantees (e.g. compliance requirements, regulated environments),
pin to a specific commit SHA instead:

```yaml
uses: ITlusions/ITL.Github/.github/workflows/_reusable-ci-python.yml@a1b2c3d
```

To find the current SHA:
```bash
git -C /path/to/ITL.Github rev-parse HEAD
# or
gh api repos/ITlusions/ITL.Github/commits/main --jq '.sha'
```

## Backward Compatibility Rules

When modifying a reusable workflow:

| Change type | Required action |
|---|---|
| Adding a new **optional** input with a default | Safe — no consumer changes needed |
| Adding a new **required** input | Breaking — update all callers first |
| Renaming or removing an input | Breaking — deprecate first, then remove |
| Changing job names or output names | Breaking — may break `needs.<job>.outputs` in callers |
| Adding a new job | Safe — callers ignore unknown jobs |

## Changelog

Breaking changes are noted in commit messages with `feat!:` or `fix!:` (conventional commits).
Search the commit history for `!:` to find all breaking changes:

```bash
gh api repos/ITlusions/ITL.Github/commits --jq '.[].commit.message' | grep '!:'
```
