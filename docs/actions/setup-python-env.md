# Setup Python Environment

**File:** `actions/setup-python-env/action.yml`

Composite action that sets up Python, configures pip caching, installs dependencies
from a requirements file, and optionally runs an additional install command.

## Steps

1. `actions/setup-python@v5` with pip cache enabled
2. `pip install -r <requirements-file>` (if file exists)
3. Run `extra-install` command (if provided)

## Inputs

| Input | Default | Description |
|---|---|---|
| `python-version` | `3.12` | Python version to install |
| `requirements-file` | `requirements.txt` | Path to requirements file for pip cache key and install |
| `extra-install` | `""` | Additional pip install command, e.g. `pip install -e .` |
| `working-directory` | `.` | Working directory for all steps |

## Outputs

| Output | Description |
|---|---|
| `python-version` | Installed Python version string |

## Usage

```yaml
steps:
  - uses: actions/checkout@v4

  - uses: ITlusions/ITL.Github/actions/setup-python-env@main
    with:
      python-version: "3.12"
      requirements-file: "requirements.txt"
      extra-install: "pip install -e ."

  - run: pytest tests/
```

## Notes

- If `requirements-file` does not exist, the install step is skipped silently.
- The pip cache key is based on `requirements-file`, so changing that file invalidates the cache.
