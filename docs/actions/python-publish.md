# Composite Action: Python Publish

**File**: `actions/python-publish/action.yml`  
**Type**: Composite action  
**Location**: ITL.Github  
**Reusability**: Can be used in any repo (unlike reusable workflows)

## Overview

Composite action for building, attesting, and publishing Python packages to PyPI with full supply chain security (SBOM + Sigstore attestation) and GitHub Release integration.

**Why composite?** Works with OIDC Trusted Publishing (reusable workflows don't).

## When to Use

✅ **Use for:**
- Publishing Python packages with Trusted Publisher auth
- Repos that need reusability + OIDC support
- Custom publish workflows in individual repos
- Consistent build → attest → publish → release flow

❌ **Don't use for:**
- Shared workflows across many repos (use `_reusable-python-publish.yml` instead)
- Non-Python projects
- Projects without GitHub Releases

## How to Reference

### In Your Workflow

```yaml
# .github/workflows/publish.yml (in your repo)
name: Publish

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    environment:
      name: pypi
    permissions:
      contents: read
      id-token: write

    steps:
    - uses: actions/checkout@v4.3.0
      with:
        fetch-depth: 0

    - name: Publish Python package
      uses: ITlusions/ITL.Github/actions/python-publish@v0.2.5
      with:
        python_version: '3.12'
        publish_to: 'pypi'
        upload_to_release: 'true'
```

## Input Parameters

### `python_version`
- **Type**: `string`
- **Default**: `'3.12'`
- **Required**: No
- **Description**: Python version to use for building
- **Examples**: `'3.11'`, `'3.12'`, `'3.13'`

### `publish_to`
- **Type**: `string`
- **Default**: None
- **Required**: Yes
- **Allowed**: `'pypi'` | `'testpypi'` | `'none'`
- **Description**: Target PyPI repository
- **Examples**: 
  - `'pypi'` → Production PyPI
  - `'testpypi'` → Test PyPI
  - `'none'` → Skip publishing

### `testpypi_url`
- **Type**: `string`
- **Default**: `'https://test.pypi.org/legacy/'`
- **Required**: No
- **Description**: TestPyPI repository URL
- **Note**: Usually leave as default

### `pypi_url`
- **Type**: `string`
- **Default**: `'https://upload.pypi.org/legacy/'`
- **Required**: No
- **Description**: PyPI repository URL
- **Note**: Usually leave as default

### `upload_to_release`
- **Type**: `string`
- **Default**: `'false'`
- **Required**: No
- **Allowed**: `'true'` | `'false'`
- **Description**: Upload built artifacts to GitHub Release
- **Examples**:
  - `'true'` → Attach `.whl`, `.tar.gz`, and SBOM to release
  - `'false'` → Skip release upload

## What It Does (Step-by-Step)

### 1. Set Up Python
Installs specified Python version using `actions/setup-python@v5`.

### 2. Build Distribution
```bash
python -m pip install --upgrade pip build
python -m build
# Creates:
#   dist/your-package-1.0.0.whl
#   dist/your-package-1.0.0.tar.gz
```

### 3. Generate SBOM (CycloneDX)
```bash
# Scans dependencies, creates sbom.cyclonedx.json
# Format: OWASP CycloneDX (industry standard)
```

**SBOM Contents**:
- All direct + transitive dependencies
- Version numbers
- License information
- Download URLs

**Use cases**:
- Vulnerability scanning (Grype, Trivy)
- License compliance (FOSSA, Black Duck)
- Supply chain analysis

### 4. Attest Build Provenance
Creates Sigstore-signed attestation proving CI built the wheels.

**Public repos**: ✅ Uses free Sigstore (automatic)
**Private repos**: ❌ Requires GitHub Enterprise Cloud

**Attestation proves**:
- Builder: your CI workflow
- Commit SHA
- Timestamp
- Artifact digest

### 5. Publish to PyPI/TestPyPI
Uses `pypa/gh-action-pypi-publish@release/v1` with OIDC tokens.

### 6. Upload SBOM as Artifact
Stores `sbom.cyclonedx.json` in GitHub Actions artifacts (90-day retention).

### 7. Upload to GitHub Release (Optional)
If `upload_to_release: 'true'`, attaches to the release:
- `dist/*.whl` — Python wheels
- `dist/*.tar.gz` — Source distributions  
- `sbom.cyclonedx.json` — Bill of materials

## Example Workflows

### Example 1: Release to PyPI with SBOM

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    environment:
      name: pypi
    permissions:
      contents: read
      id-token: write

    steps:
    - uses: actions/checkout@v4.3.0
      with:
        fetch-depth: 0

    - name: Publish
      uses: ITlusions/ITL.Github/actions/python-publish@v0.2.5
      with:
        python_version: '3.12'
        publish_to: 'pypi'
        upload_to_release: 'true'
```

**Result**: 
- Package on PyPI
- Attestations verifiable via `gh attestation verify`
- SBOM + wheels attached to GitHub Release
- SBOM in Actions artifacts (90 days)

### Example 2: Prerelease to TestPyPI

```yaml
name: Publish Prerelease

on:
  push:
    branches: [main]

jobs:
  publish:
    runs-on: ubuntu-latest
    environment:
      name: testpypi
    permissions:
      contents: read
      id-token: write

    steps:
    - uses: actions/checkout@v4.3.0

    - name: Publish prerelease
      uses: ITlusions/ITL.Github/actions/python-publish@v0.2.5
      with:
        python_version: '3.12'
        publish_to: 'testpypi'
        testpypi_url: 'https://test.pypi.org/legacy/'
        upload_to_release: 'false'
```

### Example 3: Build Only (No Publish)

```yaml
- name: Build artifacts
  uses: ITlusions/ITL.Github/actions/python-publish@v0.2.5
  with:
    python_version: '3.12'
    publish_to: 'none'
    upload_to_release: 'false'
```

**Result**: 
- Wheels built
- SBOM generated
- Attestation created
- Nothing published (useful for dry-runs)

## Authentication

### OIDC Trusted Publisher

Requires OIDC Trusted Publisher configured on PyPI/TestPyPI:

```yaml
environment:
  name: pypi
permissions:
  id-token: write  # Critical!
```

**Setup on PyPI**:
1. Go to PyPI → Settings → Publishing → Trusted Publishers
2. Add new trusted publisher:
   - Type: GitHub
   - Repository: `ITlusions/{YourRepo}`
   - Workflow: `.github/workflows/publish.yml`
   - Environment: `pypi`
3. Repeat for TestPyPI with environment: `testpypi`

### How It Works

1. GitHub generates OIDC token with workflow claims
2. Token sent to PyPI during `gh-action-pypi-publish` action
3. PyPI verifies token matches trusted publisher config
4. If match: ✅ publish allowed | If mismatch: ❌ error

## Troubleshooting

### "invalid-publisher: no corresponding publisher"

**Cause**: Trusted publisher not configured or workflow path mismatch.

**Fix**:
```yaml
# Ensure your workflow path matches PyPI config
# Bad: .github/workflows/ci.yml (PyPI expects publish.yml)
# Good: .github/workflows/publish.yml (matches PyPI)
```

### "Attestation failed on private repo"

**Cause**: Private repos need GitHub Enterprise Cloud for attestation.

**Fix**: Add `continue-on-error` to attestation step (built into action).

### "SBOM not found in release"

**Cause**: `upload_to_release: 'false'` or not a release event.

**Fix**: Set to `'true'` and ensure workflow triggered on `release` event.

## Version Pinning

Always pin to a specific tag:

```yaml
# ✅ Good
uses: ITlusions/ITL.Github/actions/python-publish@v0.2.5

# ❌ Avoid
uses: ITlusions/ITL.Github/actions/python-publish@main
```

Latest version: **v0.2.5**

## Integration with Pipeline

### With Reusable CI Template

```yaml
name: Pipeline

on:
  release:
    types: [published]

jobs:
  ci:
    uses: ITlusions/ITL.Github/.github/workflows/_reusable-python-ci.yml@v0.2.5

  publish:
    needs: ci
    runs-on: ubuntu-latest
    environment:
      name: pypi
    permissions:
      contents: read
      id-token: write
    steps:
    - uses: actions/checkout@v4.3.0
    - uses: ITlusions/ITL.Github/actions/python-publish@v0.2.5
      with:
        python_version: '3.12'
        publish_to: 'pypi'
        upload_to_release: 'true'
```

## Related Documentation

- [Reusable Python Publish Workflow](./reusable-python-publish.md)
- [Reusable Python CI Workflow](./reusable-python-ci.md)
- [Build Provenance Attestation (GitHub Docs)](https://docs.github.com/en/actions/security-guides/using-artifact-attestations-to-establish-provenance-for-builds)
- [SBOM in GitHub (CycloneDX)](https://github.com/anchore/sbom-action)
