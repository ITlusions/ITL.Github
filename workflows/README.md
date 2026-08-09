# Reusable Workflows

This folder contains reusable GitHub Actions workflows for Python projects across the ITL organization.

## Available Templates

### 1. **_reusable-python-ci.yml**
Comprehensive CI pipeline for Python packages:
- **Test**: Import validation + dependency checks
- **Lint**: Black formatting, mypy type checking, ruff linter, bandit security scan
- **Build**: Automatic wheel building with dynamic artifact naming

**Usage:**
```yaml
jobs:
  ci:
    uses: ITlusions/ITL.Github/.github/workflows/_reusable-python-ci.yml@main
    with:
      python_version: '3.12'
      test_import_path: 'your_package.core.config'
      test_import_class: 'Settings'
      src_directory: 'src'
```

**Inputs:**
- `python_version` (default: '3.12'): Python version to use
- `test_import_path` (default: 'itl_braincell_sdk.core.config'): Import path for import validation
- `test_import_class` (default: 'Settings'): Class/module name to import
- `src_directory` (default: 'src'): Directory for linting

**Artifacts:**
- Wheel artifact with branch-aware naming:
  - `main`: `wheel-v{TAG}`
  - `develop`: `wheel-v{TAG}-development`
  - `feature/**`: `wheel-v{TAG}-{BRANCH}-{SHORT_SHA}`
  - `hotfix/**`: `wheel-v{TAG}-{BRANCH}-{SHORT_SHA}`

---

### 2. **_reusable-python-publish.yml**
Intelligent PyPI publishing with automatic branch detection:
- **Automatic Publishing**: Push to `feature/**` → TestPyPI, `hotfix/**` → PyPI
- **Release Publishing**: GitHub Release (prerelease: true) → TestPyPI, (false) → PyPI
- **Manual Override**: workflow_dispatch with `publish_target` input (auto, testpypi, pypi)
- **OIDC Authentication**: Trusted Publisher for secure PyPI auth

**Usage:**
```yaml
jobs:
  publish:
    uses: ITlusions/ITL.Github/.github/workflows/_reusable-python-publish.yml@main
    with:
      python_version: '3.12'
    secrets: inherit
```

**Inputs:**
- `python_version` (default: '3.12'): Python version to use
- `testpypi_url` (default: 'https://test.pypi.org/legacy/'): TestPyPI URL
- `pypi_url` (default: 'https://upload.pypi.org/legacy/'): PyPI URL

**Publishing Logic:**
| Trigger | Condition | Target |
|---------|-----------|--------|
| Release | prerelease: true | TestPyPI |
| Release | prerelease: false | PyPI |
| Push | branch: feature/** | TestPyPI |
| Push | branch: hotfix/** | PyPI |
| Dispatch | publish_target: testpypi | TestPyPI |
| Dispatch | publish_target: pypi | PyPI |

---

## Setup Instructions

### 1. Create Workflows in Your Repo

Create `.github/workflows/` files in your repository:

**`.github/workflows/ci.yml`:**
```yaml
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

**`.github/workflows/publish.yml`:**
```yaml
name: Publish

on:
  release:
    types: [ published ]
  push:
    branches: [ 'feature/**', 'hotfix/**' ]
  workflow_dispatch:
    inputs:
      publish_target:
        description: 'Publish target'
        required: false
        default: 'auto'
        type: choice
        options:
          - auto
          - testpypi
          - pypi

jobs:
  publish:
    uses: ITlusions/ITL.Github/.github/workflows/_reusable-python-publish.yml@main
    with:
      python_version: '3.12'
    secrets: inherit
```

### 2. Configure setuptools-scm

Ensure your `pyproject.toml` has:

```toml
[build-system]
requires = ["setuptools>=68", "wheel", "setuptools-scm>=8"]

[project]
name = "your-package"
dynamic = ["version"]

[tool.setuptools-scm]
write_to = "src/your_package/_version.py"
write_to_template = '__version__ = "{version}"\n'
tag_regex = "^v(?P<version>\\d+\\.\\d+\\.\\d+(?:[a-zA-Z0-9\\-\\.]*)?)$"
```

### 3. Set Up PyPI OIDC

1. Go to PyPI/TestPyPI settings
2. Add trusted publisher:
   - GitHub repository: `ITlusions/{YourRepo}`
   - Workflow filename: `.github/workflows/publish.yml`
   - Environment name: `pypi`

### 4. Tag Releases

Create git tags for releases:
```bash
git tag v1.0.0
git push origin v1.0.0
```

---

## Examples

### Example 1: Feature Branch → TestPyPI
```bash
git checkout -b feature/new-feature
# ... make changes ...
git push origin feature/new-feature
# → Automatically publishes to TestPyPI with prerelease version
```

### Example 2: Hotfix Branch → PyPI Stable
```bash
git checkout -b hotfix/critical-fix
# ... make changes ...
git push origin hotfix/critical-fix
# → Automatically publishes to PyPI stable
```

### Example 3: GitHub Release
```bash
gh release create v2.0.0 --generate-notes
# prerelease: false → Publishes to PyPI
gh release create v2.0.0-rc1 --generate-notes --prerelease
# prerelease: true → Publishes to TestPyPI
```

---

## Implementation Details

### Version Source
- **Only git tags** via `setuptools-scm`
- **No file parsing** whatsoever
- Tag pattern: `v*.*.* ` (e.g., v1.0.0, v2.0.1-rc1)

### Environment (OIDC)
- **Critical**: Publish workflow MUST have `environment: name: pypi`
- Authenticates via Trusted Publisher (no API tokens)
- OIDC claims include repo + workflow + branch verification

### Artifact Naming
- Dynamic based on branch and latest git tag
- Main/release branches: `wheel-v{TAG}`
- Development branch: `wheel-v{TAG}-development`
- Feature/hotfix branches: `wheel-v{TAG}-{BRANCH}-{SHORT_SHA}`

---

## Troubleshooting

### "invalid-publisher: valid token, but no corresponding publisher"
**Solution**: Ensure `environment: name: pypi` is in the publish job. Check PyPI settings for trusted publisher.

### "tag_regex did not match"
**Solution**: Ensure git tag matches pattern `v#.#.#` (e.g., `v1.0.0`, not `1.0.0` or `version-1.0.0`).

### "No version found"
**Solution**: 
1. Ensure git tag exists: `git tag -l`
2. Ensure `setuptools-scm` is in build-system requires
3. Ensure `dynamic = ["version"]` in pyproject.toml

### Import validation fails
**Solution**: Check `test_import_path` and `test_import_class` match your package structure.

---

## See Also

- [ITL.Braincell.SDK](https://github.com/ITlusions/ITL.Braincell.SDK) — Reference implementation
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [setuptools-scm Documentation](https://setuptools-scm.readthedocs.io/)
- [PyPI Trusted Publisher](https://docs.pypi.org/trusted-publishers/)
