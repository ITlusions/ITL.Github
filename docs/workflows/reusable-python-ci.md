# Reusable Python CI Template

**File**: `.github/workflows/_reusable-python-ci.yml`  
**Location**: ITL.Github  
**Type**: Reusable workflow (workflow_call)

## Overview

Comprehensive CI pipeline for Python packages with test, lint, and build stages. Designed for organization-wide use across all ITL Python projects.

## When to Use

✅ **Use for:**
- Python packages that need testing before release
- Projects with `pyproject.toml` and `setup.py`
- Any project requiring linting and type checking
- Projects publishing to PyPI/TestPyPI

❌ **Don't use for:**
- Non-Python projects
- Projects without a standard package structure
- Docker-only workflows (use ci-docker.md instead)

## How to Reference

```yaml
# .github/workflows/ci.yml (in your repo)
name: CI

on:
  pull_request:
    branches: [ main, develop ]
  push:
    branches: [ main, develop, 'release/**', 'feature/**', 'hotfix/**' ]
  workflow_dispatch:

jobs:
  ci:
    uses: ITlusions/ITL.Github/.github/workflows/_reusable-python-ci.yml@main
    with:
      python_version: '3.12'
      test_import_path: 'your_package.core'
      test_import_class: 'YourClass'
      src_directory: 'src'
```

## Input Parameters

### `python_version`
- **Type**: `string`
- **Default**: `'3.12'`
- **Description**: Python version to use for testing and linting
- **Examples**: `'3.11'`, `'3.12'`, `'3.13'`

### `test_import_path`
- **Type**: `string`
- **Default**: `'itl_braincell_sdk.core.config'`
- **Description**: Full import path for validation test (e.g., `package.module.submodule`)
- **Used in**: `from {test_import_path} import {test_import_class}`
- **Examples**:
  - `'itl_braincell_sdk.core.config'`
  - `'my_package.services.api'`
  - `'braincell.core'`

### `test_import_class`
- **Type**: `string`
- **Default**: `'Settings'`
- **Description**: Class or module name to import (validates package structure)
- **Used in**: `from {test_import_path} import {test_import_class}`
- **Examples**:
  - `'Settings'`
  - `'ApiClient'`
  - `'utils'`

### `src_directory`
- **Type**: `string`
- **Default**: `'src'`
- **Description**: Root directory containing source code (for linting)
- **Examples**:
  - `'src'`
  - `'lib'`
  - `'itl_braincell_sdk'`

## Jobs

### Job 1: `test`
**Duration**: ~30-40 seconds

Validates package structure and dependencies:
1. Checkout code
2. Set up Python environment
3. Cache pip packages (speeds up repeated runs)
4. Install package with dev dependencies: `pip install -e ".[dev]"`
5. Import validation: `from {test_import_path} import {test_import_class}`

**Fails if:**
- Import path doesn't exist
- Required dependencies are missing
- Package structure is invalid

**Output**: ✅ Green check or ❌ Red X

### Job 2: `lint`
**Duration**: ~15-20 seconds

Code quality and security scanning (all non-blocking):
1. **Black** - Code formatting check: `black --check {src_directory}`
2. **mypy** - Type checking: `mypy {src_directory} --ignore-missing-imports`
3. **ruff** - Linting and style: `ruff check {src_directory}`
4. **bandit** - Security scanning: `bandit -r {src_directory}`

**Note**: All checks run with `|| true` (non-blocking). Pipeline continues even if any check fails.

**Output**: Warnings and suggestions (doesn't block merge)

### Job 3: `build`
**Duration**: ~10-15 seconds  
**Depends on**: `test` and `lint` pass

Builds Python wheel package:
1. Checkout code (fetch full history for git tags)
2. Set up Python
3. Detect version from git tags: `git describe --tags --abbrev=0`
4. Generate artifact name based on branch:
   - **main**: `wheel-v{TAG}`
   - **develop**: `wheel-v{TAG}-development`
   - **release/\***: `wheel-v{TAG}`
   - **feature/\***: `wheel-v{TAG}-{BRANCH}-{SHORT_SHA}`
   - **hotfix/\***: `wheel-v{TAG}-{BRANCH}-{SHORT_SHA}`
5. Build wheel: `python -m build`
6. Upload artifact (30-day retention)

**Output**: 
- Artifact available for download
- Ready for publishing by publish template

## Artifact Naming

Artifacts follow this pattern for easy identification:

| Branch | Pattern | Example |
|--------|---------|---------|
| `main` | `wheel-v{TAG}` | `wheel-v1.0.0` |
| `develop` | `wheel-v{TAG}-development` | `wheel-v1.0.0-development` |
| `release/v2.0` | `wheel-v{TAG}` | `wheel-v2.0.0-rc1` |
| `feature/auth` | `wheel-v{TAG}-{BRANCH}-{SHA}` | `wheel-v1.0.0-feature-auth-a1b2c3d` |
| `hotfix/bug` | `wheel-v{TAG}-{BRANCH}-{SHA}` | `wheel-v1.0.0-hotfix-bug-x9y8z7w` |

## Version Detection

✅ **Supported**:
- Git tags matching `v*.*.* ` (e.g., `v1.0.0`, `v2.0.1`)
- Detected via: `git describe --tags --abbrev=0`
- Configured in `setuptools-scm` in `pyproject.toml`

❌ **Not supported**:
- Version hardcoded in `__init__.py`
- Version in `setup.cfg`
- File parsing of any kind

## pyproject.toml Requirements

```toml
[build-system]
requires = ["setuptools>=68", "wheel", "setuptools-scm>=8"]

[project]
name = "your-package-name"
dynamic = ["version"]

[tool.setuptools-scm]
write_to = "src/your_package/_version.py"
write_to_template = '__version__ = "{version}"\n'
tag_regex = "^v(?P<version>\\d+\\.\\d+\\.\\d+(?:[a-zA-Z0-9\\-\\.]*)?)$"

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-asyncio>=0.21",
    "pytest-cov>=4.0",
    "black>=23.0",
    "mypy>=1.0",
    "ruff>=0.1",
    "bandit>=1.7",
]
```

## Example Usage

### Example 1: Basic Setup (Default Settings)

```yaml
# .github/workflows/ci.yml
jobs:
  ci:
    uses: ITlusions/ITL.Github/.github/workflows/_reusable-python-ci.yml@main
```

Uses all defaults:
- Python 3.12
- Imports from: `itl_braincell_sdk.core.config`
- Imports: `Settings`
- Lint source: `src/`

### Example 2: Custom Settings

```yaml
# .github/workflows/ci.yml
jobs:
  ci:
    uses: ITlusions/ITL.Github/.github/workflows/_reusable-python-ci.yml@main
    with:
      python_version: '3.13'
      test_import_path: 'my_api.services.database'
      test_import_class: 'DatabaseConnection'
      src_directory: 'lib'
```

## Troubleshooting

### "ModuleNotFoundError: No module named '{path}'"

**Problem**: `test_import_path` or `test_import_class` is incorrect

**Solution**:
1. Verify import path: `python -c "from your.path import YourClass"`
2. Check package structure
3. Ensure `pyproject.toml` lists all dependencies

### "No module named 'black' / 'mypy' / 'ruff' / 'bandit'"

**Problem**: Dev dependencies not installed

**Solution**: Add these to `pyproject.toml`:
```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-asyncio>=0.21",
    "pytest-cov>=4.0",
    "black>=23.0",
    "mypy>=1.0",
    "ruff>=0.1",
    "bandit>=1.7",
]
```

### "No tags found" or "tag_regex did not match"

**Problem**: No git tags or wrong tag format

**Solution**:
1. Create git tags: `git tag v1.0.0 && git push origin v1.0.0`
2. Tag format must be: `v#.#.#` (e.g., `v1.0.0`, `v2.0.0-rc1`)
3. Verify setuptools-scm config in `pyproject.toml`

### Linting fails but CI still passes

**Problem**: This is intentional! All lint checks run with `|| true` (non-blocking)

**Solution**: Review lint output and fix issues before merging, or adjust `pyproject.toml` tool configs:
```toml
[tool.black]
line-length = 88
target-version = ["py312"]

[tool.mypy]
python_version = "3.12"
warn_return_any = true

[tool.ruff]
line-length = 88
target-version = "py312"
```

## Related Templates

- [`_reusable-python-publish.yml`](reusable-python-publish.md) - Publish to PyPI/TestPyPI
- [`ci-docker.md`](ci-docker.md) - CI for Docker images
- [`publish-pypi.md`](publish-pypi.md) - PyPI publishing details

## See Also

- [ITL.Braincell.SDK](https://github.com/ITlusions/ITL.Braincell.SDK) — Reference implementation
- [setuptools-scm Docs](https://setuptools-scm.readthedocs.io/)
- [GitHub Actions: workflow_call](https://docs.github.com/en/actions/using-workflows/reusing-workflows)
