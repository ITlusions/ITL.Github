# Reusable Python Publish Template

**File**: `.github/workflows/_reusable-python-publish.yml`  
**Location**: ITL.Github  
**Type**: Reusable workflow (workflow_call)

## Overview

Intelligent PyPI publishing with automatic branch-based targeting, supply chain security (SBOM + attestation), and GitHub Release management. Publishes to:
- **PyPI (stable)** for production releases
- **TestPyPI (prerelease)** for testing and development

Features:
- 📦 **Build & Package** — Python wheels + source distributions
- 📋 **SBOM** — CycloneDX Software Bill of Materials (all repos)
- 🔐 **Attestation** — Sigstore build provenance (public repos)
- 📤 **Release Upload** — Attach artifacts to GitHub Release
- 🔀 **Smart Routing** — Automatic branch-based targeting

Supports automatic detection or manual override via workflow_dispatch.

## When to Use

✅ **Use for:**
- Publishing Python packages to PyPI
- Separating stable vs prerelease releases
- Automatic branch-based publishing (feature → TestPyPI, hotfix → PyPI)
- OIDC Trusted Publisher authentication

❌ **Don't use for:**
- Non-Python packages
- Manual PyPI authentication via API tokens
- Projects not on GitHub

## How to Reference

```yaml
# .github/workflows/publish.yml (in your repo)
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

## Input Parameters

### `python_version`
- **Type**: `string`
- **Default**: `'3.12'`
- **Description**: Python version for building and publishing
- **Examples**: `'3.11'`, `'3.12'`, `'3.13'`

### `testpypi_url`
- **Type**: `string`
- **Default**: `'https://test.pypi.org/legacy/'`
- **Description**: TestPyPI repository URL
- **Usually**: Leave as default (don't change)

### `pypi_url`
- **Type**: `string`
- **Default**: `'https://upload.pypi.org/legacy/'`
- **Description**: PyPI repository URL
- **Usually**: Leave as default (don't change)

## Publishing Logic

### Automatic Detection (How It Decides Where to Publish)

The template automatically determines the publish target based on trigger type and branch:

#### 1. GitHub Release Event
```
IF release created:
  IF prerelease: true  → TestPyPI (prerelease)
  IF prerelease: false → PyPI (stable production)
```

**Usage**:
```bash
# Publish to PyPI (stable)
gh release create v2.0.0 --generate-notes

# Publish to TestPyPI (prerelease)
gh release create v2.0.0-rc1 --generate-notes --prerelease
```

#### 2. Push to Feature/Hotfix Branch
```
IF push to branch:
  IF feature/** → TestPyPI (prerelease)
  IF hotfix/**  → PyPI (stable)
```

**Usage**:
```bash
# Automatic TestPyPI publish
git checkout -b feature/new-feature
git push origin feature/new-feature
# → Automatically publishes to TestPyPI

# Automatic PyPI publish
git checkout -b hotfix/critical-bug
git push origin hotfix/critical-bug
# → Automatically publishes to PyPI
```

#### 3. Manual Dispatch Override
```
IF workflow_dispatch with publish_target input:
  IF publish_target: auto    → Use branch detection (feature/** or hotfix/**)
  IF publish_target: testpypi → Force TestPyPI
  IF publish_target: pypi     → Force PyPI
```

**Usage**:
```bash
# Trigger manually from GitHub UI or CLI
gh workflow run publish.yml -f publish_target=testpypi
gh workflow run publish.yml -f publish_target=pypi
```

## Jobs

### Job 1: `determine_target`
**Duration**: ~5 seconds

Evaluates trigger type and branch to decide publish destination:

**Outputs**:
- `publish_to` — Target repository: `pypi` | `testpypi` | `none`
- `publish_reason` — Human-readable reason for decision

**Decision Tree**:
```
GitHub Release?
  ├─ prerelease: true  → publish_to=testpypi, reason="GitHub Release (prerelease)"
  └─ prerelease: false → publish_to=pypi, reason="GitHub Release (stable)"

Push event?
  ├─ feature/** → publish_to=testpypi, reason="Automatic: feature branch"
  ├─ hotfix/**  → publish_to=pypi, reason="Automatic: hotfix branch"
  └─ other      → publish_to=none, reason="Branch not configured for publishing"

Manual dispatch?
  ├─ publish_target=auto
  │  ├─ feature/** → publish_to=testpypi, reason="Manual override (auto): feature"
  │  ├─ hotfix/**  → publish_to=pypi, reason="Manual override (auto): hotfix"
  │  └─ other      → publish_to=none, reason="Branch not configured"
  ├─ publish_target=testpypi → publish_to=testpypi, reason="Manual override: testpypi"
  └─ publish_target=pypi → publish_to=pypi, reason="Manual override: pypi"
```

### Job 2: `publish`
**Duration**: ~20-30 seconds  
**Depends on**: `determine_target` outputs  
**Condition**: Only runs if `publish_to != 'none'`

Builds, secures, and publishes package:

1. **Checkout code** (fetch full history for git tags)
2. **Set up Python** (specified version)
3. **Build distribution**:
   - Install build tools: `pip install build`
   - Build wheel: `python -m build`
   - Creates `dist/` with `.whl` and `.tar.gz` files
4. **Generate SBOM (CycloneDX)**:
   - Uses `anchore/sbom-action@v0`
   - Scans dependencies and generates `sbom.cyclonedx.json`
   - Works on **all repos** (public & private)
   - File format: CycloneDX (OWASP standard)
5. **Attest build provenance**:
   - Uses `actions/attest-build-provenance@v1`
   - Generates Sigstore-signed attestations
   - ✅ Works on **public repos** (free, auto-Sigstore)
   - ❌ Private repos need GitHub Enterprise Cloud
   - Binds artifact digest to SLSA provenance
6. **Publish to TestPyPI** (if `publish_to == testpypi`):
   - Uses `pypa/gh-action-pypi-publish@release/v1`
   - Publishes to `https://test.pypi.org/legacy/`
   - `continue-on-error: true` (doesn't fail main workflow)
7. **Publish to PyPI** (if `publish_to == pypi`):
   - Uses `pypa/gh-action-pypi-publish@release/v1`
   - Publishes to `https://upload.pypi.org/legacy/`
   - `continue-on-error: true` (doesn't fail main workflow)
8. **Upload SBOM artifact**:
   - Stores `sbom.cyclonedx.json` to GitHub Actions artifacts
   - 90-day retention
   - Downloadable via `gh run download`
9. **Upload to GitHub Release** (only on GitHub Release events):
   - Attaches all distributions + SBOM to GitHub Release
   - Files: `*.whl`, `*.tar.gz`, `sbom.cyclonedx.json`
10. **Print result** (logs publish target and reason)

**Output**: 
- Package on PyPI/TestPyPI
- Attestations in GitHub (verify: `gh attestation verify`)
- SBOM stored in artifacts
- Release assets attached to GitHub Release

## Supply Chain Security

### SBOM (Software Bill of Materials)

**What it does**: Lists all dependencies, versions, and licenses in CycloneDX format.

**Available on**: ✅ All repos (public & private)

**Usage**:
```bash
# Download SBOM from workflow run
gh run download <run-id> --name sbom
cat sbom.cyclonedx.json | jq '.components[] | {name, version, licenses}'

# Analyze for known vulnerabilities
# (Use with: Dependency-Track, Grype, Trivy, etc.)
```

### Build Provenance Attestation

**What it does**: Creates signed proof that wheels were built by your CI workflow (SLSA L2+).

**Available on**: ✅ Public repos | ❌ Private repos (needs GitHub Enterprise)

**Usage**:
```bash
# Verify attestation
gh attestation verify dist/braincell-*.whl

# Output shows:
# - Builder: github.com/ITlusions/ITL.Braincell.SDK/.github/workflows/publish.yml@v2.0.0
# - Commit SHA
# - Provenance digest
```

**Why it matters**:
- 🔐 Proves artifact integrity (not tampered)
- ✅ SLSA compliance (Software Supply Chain Levels for Secure Software)
- 🔍 Verifiable by downstream consumers
- 📋 Audit trail for compliance requirements

## Authentication: OIDC Trusted Publisher

This template uses **GitHub OIDC Trusted Publisher** for authentication (no API tokens):

### ⚠️ Critical Setup

Your workflow **MUST** have:
```yaml
jobs:
  publish:
    environment:
      name: pypi
    permissions:
      contents: read
      id-token: write
```

✅ This template already includes both. But if you modify it, don't remove these!

### PyPI/TestPyPI Configuration

1. Go to **PyPI Settings** → **Publishing** → **Trusted Publishers**
2. Click **"Add a new Trusted Publisher"**
3. Select **GitHub** as publisher type
4. Fill in:
   - **Repository name**: `ITlusions/{YourRepo}`
   - **Workflow filename**: `.github/workflows/publish.yml`
   - **Environment name**: `pypi`
5. Click **"Add Trusted Publisher"**

**Do this for BOTH PyPI and TestPyPI** (separate trusted publishers).

### How It Works

1. GitHub generates an OIDC token with claims:
   - Repository: `github.repository`
   - Workflow file: `.github/workflows/publish.yml`
   - Environment: `pypi`
   - Branch: current branch
2. Token sent to PyPI/TestPyPI
3. PyPI/TestPyPI verifies claims match trusted publisher config
4. If match: authentication successful → publish allowed
5. If mismatch: authentication fails → "invalid-publisher" error

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
```

**Important**: 
- `dynamic = ["version"]` required (not hardcoded)
- `tag_regex` must match your git tag format
- setuptools-scm must be in build requirements

## Example Workflows

### Example 1: Automatic Feature → TestPyPI

```yaml
# Your feature branch
git checkout -b feature/auth-system
# Make changes
git push origin feature/auth-system

# Workflow triggers automatically:
# → publish.yml detects push to feature/**
# → determine_target outputs: publish_to=testpypi
# → Package published to TestPyPI with prerelease version
# → Installable via: pip install --index-url https://test.pypi.org/simple/ your-package
```

### Example 2: Automatic Hotfix → PyPI

```yaml
# Your hotfix branch
git checkout -b hotfix/critical-db-bug
# Make changes
git push origin hotfix/critical-db-bug

# Workflow triggers automatically:
# → publish.yml detects push to hotfix/**
# → determine_target outputs: publish_to=pypi
# → Package published to PyPI (stable)
# → Installable via: pip install your-package
```

### Example 3: GitHub Release → Based on Prerelease Flag

```yaml
# Stable release
gh release create v2.0.0 --generate-notes
# → prerelease: false
# → publish_to=pypi (stable)
# → Installable: pip install your-package

# Release candidate
gh release create v2.0.0-rc1 --generate-notes --prerelease
# → prerelease: true
# → publish_to=testpypi (prerelease)
# → Installable: pip install --index-url https://test.pypi.org/simple/ your-package==2.0.0rc1
```

### Example 4: Manual Override

```bash
# Force publish to TestPyPI even from main/develop
gh workflow run publish.yml -f publish_target=testpypi

# Force publish to PyPI from anywhere
gh workflow run publish.yml -f publish_target=pypi

# Use branch detection
gh workflow run publish.yml -f publish_target=auto
```

## Troubleshooting

### "invalid-publisher: valid token, but no corresponding publisher"

**Problem**: OIDC Trusted Publisher not configured, or environment name mismatch

**Solution**:
1. Go to PyPI/TestPyPI Settings → Publishing → Trusted Publishers
2. Add trusted publisher with:
   - Repository: `ITlusions/{YourRepo}`
   - Workflow: `.github/workflows/publish.yml`
   - Environment: `pypi`
3. Ensure workflow has: `environment: name: pypi`

### "Package already exists" on TestPyPI

**Problem**: Trying to upload duplicate version

**Solution**: 
- Increment version in git tag: `v1.0.1` instead of `v1.0.0`
- Or delete old version from TestPyPI manually

### "No module named 'setuptools_scm'"

**Problem**: Build system missing setuptools-scm

**Solution**: Update `pyproject.toml`:
```toml
[build-system]
requires = ["setuptools>=68", "wheel", "setuptools-scm>=8"]
```

### "publish_to=none" — Nothing Published

**Problem**: Branch not recognized for publishing

**Causes**:
- Push to `main` or `develop` (these branches don't auto-publish)
- Branch doesn't match `feature/**` or `hotfix/**` pattern
- Wrong trigger (must be `release`, `push`, or `workflow_dispatch`)

**Solution**:
- Create `feature/` or `hotfix/` branch to auto-publish
- Or use `gh workflow run` with `publish_target` override
- Or create GitHub Release

### Version Mismatch

**Problem**: Package builds as `v0.0.0` instead of current version

**Solution**:
1. Ensure git tag exists: `git tag v1.0.0 && git push origin v1.0.0`
2. Verify tag regex in `pyproject.toml`: `tag_regex = "^v(?P<version>\\d+\\.\\d+\\.\\d+...)`
3. Remove any hardcoded version from `pyproject.toml`
4. Run `git describe --tags --abbrev=0` to test tag detection

## Related Templates

- [`_reusable-python-ci.yml`](reusable-python-ci.md) - CI testing and linting
- [`publish-pypi.md`](publish-pypi.md) - PyPI publishing details
- [`detect-version.md`](detect-version.md) - Version detection strategies

## See Also

- [ITL.Braincell.SDK](https://github.com/ITlusions/ITL.Braincell.SDK) — Reference implementation
- [PyPI Trusted Publishers](https://docs.pypi.org/trusted-publishers/)
- [GitHub OIDC](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect)
- [setuptools-scm](https://setuptools-scm.readthedocs.io/)
