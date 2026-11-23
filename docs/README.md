# ITL.Github — Documentation

Central repository for reusable GitHub Actions workflows and composite actions
shared across all ITLusions repositories.

## Navigation

| Section | Description |
|---|---|
| [Getting Started](getting-started.md) | How to consume workflows and actions from another repo |
| [Versioning](versioning.md) | `@main` vs pinned refs, update strategy |
| [Workflow reference](reference/workflows/index.md) | Generated from `.github/workflows/_managed-*.yml` |
| [Action reference](reference/actions/index.md) | Generated from `actions/*/action.yml` |
| [Guide: Python Library](guides/python-library.md) | Full CI/CD pipeline for a Python package |
| [Guide: Docker Service](guides/docker-service.md) | Full CI/CD pipeline for a Docker-based service |

## Generated reference

The reference pages under `docs/reference/` and the landing-page data under
`docs/_data/generated/` are not committed. They are generated from the workflow
and action YAML files by `scripts/generate_docs.py`, which runs in the Pages
workflow before the Jekyll build.

To preview locally:

```
pip install pyyaml
python scripts/generate_docs.py
```

Inputs and outputs for each workflow and action are documented in the generated
pages. To change a description, edit the `name`, `description`, and input
definitions in the YAML file itself.
