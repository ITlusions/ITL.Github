# Getting Started

This page explains how to consume reusable workflows and composite actions from
`ITlusions/ITL.Github` in your own repository.

## Prerequisites

- Your repository is in the `ITlusions` GitHub organization, **or** `ITlusions/ITL.Github` is set to public.
- A `GH_PAT` secret is configured in your repository for workflows that require cross-repo access (e.g. checking out a dependency).

## Calling a Reusable Workflow

```yaml
jobs:
  ci:
    uses: ITlusions/ITL.Github/.github/workflows/_reusable-ci-python.yml@main
    with:
      python-version: "3.12"
      artifact-name: "myproject-wheel"
    secrets:
      gh-pat: ${{ secrets.GH_PAT }}
```

- The `with:` block maps to the `inputs:` of the called workflow.
- The `secrets:` block passes named secrets. Only secrets explicitly declared in the reusable workflow can be forwarded.
- `@main` always uses the latest version of the workflow. See [Versioning](versioning.md) for pinning strategies.

## Using a Composite Action

```yaml
steps:
  - uses: ITlusions/ITL.Github/actions/setup-python-env@main
    with:
      python-version: "3.12"
      extra-install: "pip install -e ."
```

Composite actions are used inside `steps:`, unlike reusable workflows which are used inside `jobs:`.

## Passing Secrets to Reusable Workflows

Reusable workflows only accept secrets that are explicitly declared in their `on.workflow_call.secrets` block.
You cannot forward `secrets: inherit` unless the called workflow opts in.

```yaml
jobs:
  publish:
    uses: ITlusions/ITL.Github/.github/workflows/_reusable-publish-pypi.yml@main
    with:
      artifact-name: "myproject-wheel"
      commit-sha: ${{ github.sha }}
      environment: "production"
    # No secrets needed — this workflow uses OIDC (no PAT required)
```

## Required Repository Secrets

| Secret | Used by | Purpose |
|---|---|---|
| `GH_PAT` | `_reusable-ci-docker.yml`, `_reusable-auto-tag.yml`, `_reusable-docker-retag.yml` | Cross-repo checkout and tag push |

## Permissions

Some workflows require explicit `permissions:` in the **calling** workflow file:

```yaml
jobs:
  release:
    permissions:
      contents: write   # required by _reusable-release-gh.yml
      id-token: write   # required by _reusable-publish-pypi.yml (OIDC)
      actions: read     # required to download artifacts from other runs
    uses: ITlusions/ITL.Github/.github/workflows/_reusable-release-gh.yml@main
    with:
      tag: "v1.2.3"
```

## Full Examples

- [Python library pipeline](guides/python-library.md)
- [Docker service pipeline](guides/docker-service.md)
