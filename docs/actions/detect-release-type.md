# Detect Release Type

**File:** `actions/detect-release-type/action.yml`

Composite action that inspects a semver version string and determines whether it is
a stable release or a pre-release (alpha/beta/rc).

## Detection Logic

A version is classified as pre-release if it matches `-(alpha|beta|rc)\.` — e.g.:
- `1.2.3-rc.1` → pre-release
- `1.2.3-beta.2` → pre-release
- `1.2.3-alpha.1` → pre-release
- `1.2.3` → stable

## Inputs

| Input | Required | Description |
|---|---|---|
| `version` | Yes | Semver version string, e.g. `1.2.3` or `1.2.3-rc.1` |

## Outputs

| Output | Values | Description |
|---|---|---|
| `prerelease` | `"true"` / `"false"` | Whether this is a pre-release |
| `release-type` | `"pre-release"` / `"stable"` | Human-readable release type |

## Usage

```yaml
steps:
  - uses: ITlusions/ITL.Github/actions/detect-release-type@main
    id: release-type
    with:
      version: "1.2.3-rc.1"

  - run: echo "Is pre-release: ${{ steps.release-type.outputs.prerelease }}"
  - run: echo "Type: ${{ steps.release-type.outputs.release-type }}"
```

## Notes

- This action is used internally by [`_reusable-publish-pypi.yml`](../workflows/publish-pypi.md)
  to route to PyPI vs TestPyPI.
- The version input should not include the `v` prefix.
  Strip it with `${TAG#v}` if needed.
