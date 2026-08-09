# check-md-deadlinks.ps1

Agnostic PowerShell script to scan markdown files for broken internal links (deadlinks).

## Features

✅ **Repo-agnostic** — works with any repository containing `.md` files  
✅ **Recursive scanning** — finds all markdown files automatically  
✅ **Intelligent detection** — distinguishes between:
- **File links** (`[text](path/file.md)`) — validated
- **Anchor links** (`[text](#anchor)`) — skipped (same file)
- **External URLs** (`http://`, `https://`) — skipped (not validated)
- **Relative paths** — resolved correctly across directories

✅ **Multiple output formats** — table, list, or JSON  
✅ **CI/CD ready** — exit codes and fail-on-deadlinks mode  

## Installation

Copy to your repo:
```bash
cp check-md-deadlinks.ps1 .github/scripts/
```

## Usage

### Basic scan
```bash
pwsh .github/scripts/check-md-deadlinks.ps1
```

### Scan specific directory
```bash
pwsh .github/scripts/check-md-deadlinks.ps1 -RepoRoot "D:\repos\MyRepo"
```

### Different output formats

**Table (default)**:
```bash
pwsh .github/scripts/check-md-deadlinks.ps1 -OutputFormat table
```

**List**:
```bash
pwsh .github/scripts/check-md-deadlinks.ps1 -OutputFormat list
```

**JSON** (for CI/CD):
```bash
pwsh .github/scripts/check-md-deadlinks.ps1 -OutputFormat json
```

### Fail on deadlinks (for CI/CD)
```bash
pwsh .github/scripts/check-md-deadlinks.ps1 -FailOnDeadlinks
```

Exits with code 1 if deadlinks found.

## Output Example

```
🔍 Scanning 25 markdown files for deadlinks...

📊 Summary
  Total links found: 84
  ✅ Valid: 62
  ⏭️  Skipped (external/anchor): 22
  ❌ Deadlinks: 0

✅ No deadlinks found!
```

## GitHub Actions Integration

Add to `.github/workflows/ci.yml`:

```yaml
- name: Check markdown deadlinks
  run: |
    pwsh .github/scripts/check-md-deadlinks.ps1 -FailOnDeadlinks
```

Or with JSON output for reporting:

```yaml
- name: Check markdown deadlinks
  id: deadlinks
  continue-on-error: true
  run: |
    pwsh .github/scripts/check-md-deadlinks.ps1 -OutputFormat json | Tee-Object -Variable output | ConvertFrom-Json | Select-Object -ExpandProperty deadlinks
```

## Parameters

### `-RepoRoot` (string)
- Root directory to scan
- Default: `git rev-parse --show-toplevel` (current git repo root)
- Falls back to current directory if not in a git repo

### `-OutputFormat` (string)
- Output format for results
- Options: `table`, `list`, `json`
- Default: `table`

### `-FailOnDeadlinks` (switch)
- Exit with code 1 if any deadlinks found
- Useful for CI/CD pipelines
- Default: false (exit 0 regardless)

## Exit Codes

- **0** — Success (no deadlinks or `FailOnDeadlinks` not specified)
- **1** — Deadlinks found and `FailOnDeadlinks` enabled
- **1** — No markdown files found

## What Gets Validated

✅ **Checked**:
- Relative file paths: `[text](docs/guide.md)`
- Subdirectory paths: `[text](../workflows/ci.md)`
- Paths with anchors: `[text](file.md#section)`

⏭️ **Skipped**:
- External URLs: `[text](https://github.com/...)`
- Mailto links: `[text](mailto:user@example.com)`
- Same-file anchors: `[text](#top)`
- Empty paths: `[text]()`

## Troubleshooting

### "No markdown files found"
- Check that markdown files exist in the repo
- Verify `-RepoRoot` parameter is correct

### False positives (valid links reported as dead)
- Check file path resolution
- Verify relative paths are correct
- Run with `-OutputFormat list` to see full resolved paths

### Slow scanning
- Script is typically <5 seconds for 25+ files
- For repos with 1000+ files, consider adding exclusions

## Real-World Example

ITL.Github scan result:
```
🔍 Scanning 25 markdown files for deadlinks...

📊 Summary
  Total links found: 84
  ✅ Valid: 62
  ⏭️  Skipped (external/anchor): 22
  ❌ Deadlinks: 0

✅ No deadlinks found!
```

## License

This script is part of [ITL.Github](https://github.com/ITlusions/ITL.Github).
