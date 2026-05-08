---
layout: default
title: "Real-world example: ITL.BrainCell"
---

# Real-world example: ITL.BrainCell

**ITL.BrainCell** (`itl-braincell` on PyPI) is the core library for the BrainCell persistent memory platform. It is the primary reference consumer of every reusable workflow and composite action published in this repository.

Source: [ITlusions/ITL.BrainCell](https://github.com/ITlusions/ITL.BrainCell)

---

## Pipeline chain

```
push / PR
    │
    ├── detect-version                      (all branches)
    │       _reusable-detect-version.yml
    │
    ├── ci                                  (all branches)
    │       _reusable-ci-python.yml
    │       lint (ruff) → test (pytest + postgres) → build wheel → upload artifact
    │
    ├── auto-tag                            (main + release/** only)
    │       _reusable-auto-tag.yml
    │       main:     v1.4.2 → v1.4.3
    │       release/: v1.5.0-rc.1 → v1.5.0-rc.2
    │
    └── create-release                      (main + release/** only)
            _reusable-release-gh.yml
            creates GitHub Release → attaches wheel
                        │
                        └── release: published event
                                    │
                              publish.yml
                                    │
                              _reusable-publish-pypi.yml
                              PyPI (stable) / TestPyPI (rc/beta/alpha)
```

---

## Branch behaviour

| Branch | CI | Auto-tag | Release | Publish |
|---|---|---|---|---|
| `feature/**` | lint + test + build | — | — | — |
| `hotfix/**` | lint + test + build | — | — | — |
| `develop` | lint + test + build | — | — | — |
| `release/**` | lint + test + build | `vX.Y.Z-rc.N` | Pre-release | TestPyPI |
| `main` | lint + test + build | `vX.Y.Z` | Stable | PyPI |

---

## ci.yml

The primary pipeline. Runs on every push and pull request. Builds the wheel once and uploads it as a GitHub Actions artifact named `braincell-wheel`. The downstream publish workflow downloads this exact artifact — **the wheel is never rebuilt**.

```yaml
name: CI — Build & Test

on:
  push:
    branches:
      - main
      - develop
      - "feature/**"
      - "release/**"
      - "hotfix/**"
    paths-ignore:
      - "**/*.md"
      - "docs/**"
      - ".github/agents/**"
  pull_request:
    branches:
      - main
      - develop
      - "release/**"
  workflow_dispatch:

concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true   # cancel superseded runs on the same branch

jobs:
  # ── Step 1: Resolve SemVer from git history / branch name ─────────────────
  detect-version:
    name: Detect version
    uses: ITlusions/ITL.Github/.github/workflows/_reusable-detect-version.yml@main
    # outputs: version, image-tag, python-version, is-release

  # ── Step 2: Lint → Test (+ Postgres) → Build wheel ────────────────────────
  ci:
    name: Lint / Test / Build
    needs: detect-version
    uses: ITlusions/ITL.Github/.github/workflows/_reusable-ci-python.yml@main
    with:
      python-version: "3.12"
      ref: ${{ github.sha }}
      artifact-name: "braincell-wheel"
      version: ${{ needs.detect-version.outputs.python-version }}
      ruff-src: "src/"
      test-path: "tests/"
      test-markers-exclude: "integration"   # keep CI fast; integration tests run separately
      postgres-user: "braincell"
      postgres-password: "braincell_test"
      postgres-db: "braincell_test"
      extra-install: "pip install -e ."

  # ── Step 3: Auto-tag — main and release/* only ────────────────────────────
  auto-tag:
    name: Auto-tag semver
    needs: ci
    if: |
      github.event_name == 'push' &&
      (
        github.ref == 'refs/heads/main' ||
        startsWith(github.ref, 'refs/heads/release/')
      )
    uses: ITlusions/ITL.Github/.github/workflows/_reusable-auto-tag.yml@main
    with:
      commit-sha: ${{ github.sha }}
    secrets:
      gh-pat: ${{ secrets.GH_PAT }}
    # outputs: tag  (e.g. "v0.1.4")

  # ── Step 4: Create GitHub Release — main and release/* only ───────────────
  #
  # Publishing the release is what triggers publish.yml.
  # main     → stable release  → PyPI
  # release/ → pre-release     → TestPyPI
  create-release:
    name: Create GitHub Release
    needs: auto-tag
    if: |
      github.event_name == 'push' &&
      (
        github.ref == 'refs/heads/main' ||
        startsWith(github.ref, 'refs/heads/release/')
      )
    uses: ITlusions/ITL.Github/.github/workflows/_reusable-release-gh.yml@main
    with:
      tag: ${{ needs.auto-tag.outputs.tag }}
      artifact-name: "braincell-wheel"
      generate-release-notes: true
```

---

## publish.yml

Triggered only by the `release: published` event emitted at the end of `ci.yml`. Never triggered manually or by push. Downloads the wheel from the CI run that built it — no second build.

**Authentication**: OIDC Trusted Publisher — no API tokens, no secrets stored in the repository.

```yaml
name: Publish — Release published

on:
  release:
    types: [published]

concurrency:
  group: publish-${{ github.event.release.tag_name }}
  cancel-in-progress: false   # never abort an in-flight publish

jobs:
  # ── Step 1: Determine publish target from tag name ────────────────────────
  #
  # v0.1.4          → environment: production  → PyPI
  # v0.1.4-rc.1     → environment: staging     → TestPyPI
  # v0.1.4-beta.1   → environment: staging     → TestPyPI
  resolve-target:
    name: Resolve publish target
    runs-on: ubuntu-latest
    outputs:
      environment: ${{ steps.check.outputs.environment }}
      is-prerelease: ${{ steps.check.outputs.is-prerelease }}
    steps:
      - name: Check release tag type
        id: check
        run: |
          TAG="${{ github.event.release.tag_name }}"
          if [[ "$TAG" == *"-"* ]]; then
            echo "environment=staging"    >> $GITHUB_OUTPUT
            echo "is-prerelease=true"     >> $GITHUB_OUTPUT
          else
            echo "environment=production" >> $GITHUB_OUTPUT
            echo "is-prerelease=false"    >> $GITHUB_OUTPUT
          fi

  # ── Step 2: Download CI wheel → publish ───────────────────────────────────
  publish:
    name: Publish to PyPI
    needs: resolve-target
    uses: ITlusions/ITL.Github/.github/workflows/_reusable-publish-pypi.yml@main
    with:
      artifact-name: "braincell-wheel"
      commit-sha: ${{ github.event.release.target_commitish }}
      ci-workflow-name: "CI — Build & Test"
      environment: ${{ needs.resolve-target.outputs.environment }}
```

---

## Key design decisions

### No-rebuild contract

The wheel is built exactly once in `ci.yml` and uploaded as artifact `braincell-wheel`. `publish.yml` locates the CI run by `commit-sha` and downloads the same artifact. The `_reusable-publish-pypi.yml` workflow does not call `pip wheel` or `hatch build` — it calls `twine upload` on the downloaded file.

This guarantees that the bytes published to PyPI are bit-for-bit identical to the bytes tested in CI.

### OIDC Trusted Publishing

No `PYPI_TOKEN` secret is stored in the repository. Authentication uses GitHub's OIDC token and PyPI's Trusted Publisher mechanism. The workflow file name and GitHub Environment name (`production` / `staging`) are registered on PyPI and TestPyPI.

Required PyPI configuration:

| Setting | Production | Staging |
|---|---|---|
| Owner | `ITlusions` | `ITlusions` |
| Repository | `ITL.BrainCell` | `ITL.BrainCell` |
| Workflow | `publish.yml` | `publish.yml` |
| Environment | `production` | `staging` |

### Concurrency guards

`ci.yml` uses `cancel-in-progress: true` — a new push to a branch cancels the preceding run. `publish.yml` uses `cancel-in-progress: false` — an in-flight publish is never aborted regardless of new events.

### Integration test exclusion

The `test-markers-exclude: "integration"` input to `_reusable-ci-python.yml` excludes tests marked with `@pytest.mark.integration` from the standard CI run. This keeps the CI loop fast. Integration tests are run separately in a dedicated workflow or locally via `run_tests.ps1 -TestType integration`.

---

## Required secrets

| Secret | Job | Purpose |
|---|---|---|
| `GH_PAT` | `auto-tag` | Push version tags (bypasses branch protection) |

No other secrets are required. PyPI publish uses OIDC.

---

## Required GitHub Environments

| Environment | Protection | Used by |
|---|---|---|
| `production` | Optional approval gate | publish to PyPI |
| `staging` | None | publish to TestPyPI |

---

## See also

- [Python Library Pipeline Guide](python-library) — generic template this is based on
- [Detect Version workflow](../workflows/detect-version)
- [CI — Python workflow](../workflows/ci-python)
- [Auto-tag workflow](../workflows/auto-tag)
- [GitHub Release workflow](../workflows/release-gh)
- [Publish PyPI workflow](../workflows/publish-pypi)
