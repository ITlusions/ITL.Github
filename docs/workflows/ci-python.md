# CI — Python

**File:** `_reusable-ci-python.yml`

Runs lint (ruff), tests (pytest with a PostgreSQL service), and builds a Python wheel.
The wheel is uploaded as a GitHub Actions artifact.

## Steps

1. Checkout at the specified ref
2. Patch `pyproject.toml` version (if `version` input is provided)
3. Setup Python + pip cache
4. Install dependencies (requirements.txt + optional extra)
5. Lint with ruff
6. Run pytest (with PostgreSQL available at `localhost:5432`)
7. Upload coverage report artifact
8. Build wheel (`python -m build --wheel`)
9. Upload wheel artifact

## Inputs

| Input | Type | Default | Description |
|---|---|---|---|
| `python-version` | string | `3.12` | Python version |
| `ref` | string | `""` | Git ref to check out (empty = default branch) |
| `artifact-name` | string | `python-wheel` | Name of the uploaded wheel artifact |
| `working-directory` | string | `.` | Root for ruff/pytest/build |
| `ruff-src` | string | `src/` | Directory ruff scans |
| `test-path` | string | `tests/` | Directory pytest scans |
| `test-markers-exclude` | string | `integration` | pytest `-m` expression to skip |
| `postgres-user` | string | `app` | PostgreSQL username |
| `postgres-password` | string | `app_test` | PostgreSQL password |
| `postgres-db` | string | `app_test` | PostgreSQL database name |
| `postgres-port` | string | `5432` | PostgreSQL port (informational) |
| `requirements-file` | string | `requirements.txt` | Path to requirements file for pip cache |
| `extra-install` | string | `""` | Additional pip install command, e.g. `pip install -e .` |
| `version` | string | `""` | PEP 440 version to inject into the wheel. Empty = use `pyproject.toml` as-is |

## Outputs

| Output | Description |
|---|---|
| `artifact-name` | Name of the uploaded wheel artifact |
| `version` | Version that was built into the wheel |

## Environment Variables

| Variable | Value | Set by |
|---|---|---|
| `DATABASE_URL` | `postgresql://<user>:<pass>@localhost:<port>/<db>` | Workflow |
| `ENVIRONMENT` | `test` | Workflow |
| `SETUPTOOLS_SCM_PRETEND_VERSION` | Same as `version` input | Set-version step |

## Usage

```yaml
jobs:
  detect-version:
    uses: ITlusions/ITL.Github/.github/workflows/_reusable-detect-version.yml@main

  ci:
    needs: detect-version
    uses: ITlusions/ITL.Github/.github/workflows/_reusable-ci-python.yml@main
    with:
      python-version: "3.12"
      artifact-name: "myproject-wheel"
      version: ${{ needs.detect-version.outputs.python-version }}
      ruff-src: "src/"
      test-path: "tests/"
      test-markers-exclude: "integration"
      postgres-user: "myapp"
      postgres-password: "myapp_test"
      postgres-db: "myapp_test"
      extra-install: "pip install -e ."
```

## Notes

- The PostgreSQL service is always started, even if your project does not use it.
  Tests that do not use `DATABASE_URL` are unaffected.
- `test-markers-exclude: "integration"` skips slow integration tests in CI.
  Remove this for a full test run.
- The wheel artifact name must match what downstream jobs (publish, release) expect.
