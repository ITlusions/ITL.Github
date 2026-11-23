# check-md-deadlinks.py

Agnostic Python script (standard library only) to scan markdown files for broken internal links (deadlinks).

## Features

✅ **Repo-agnostic** — works with any repository containing `.md` files  
✅ **Recursive scanning** — finds all markdown files automatically  
✅ **Intelligent detection** — distinguishes between:
- **File links** (relative `.md` paths such as `path/file.md`) — validated
- **Anchor links** (`[text](#anchor)`) — skipped (same file)
- **External URLs** (`http://`, `https://`) — skipped (not validated)
- **Relative paths** — resolved correctly across directories

✅ **Multiple output formats** — table, list, or JSON  
✅ **CI/CD ready** — exit codes and fail-on-deadlinks mode  

## Installation

Copy to your repo:
```bash
cp check-md-deadlinks.py .github/scripts/
```

Requires Python 3.10 or later. No third-party packages are needed.

## Usage

### Basic scan
```bash
python3 .github/scripts/check-md-deadlinks.py
```

### Scan specific directory
```bash
python3 .github/scripts/check-md-deadlinks.py --repo-root "D:\repos\MyRepo"
```

### Different output formats

**Table (default)**:
```bash
python3 .github/scripts/check-md-deadlinks.py --output-format table
```

**List**:
```bash
python3 .github/scripts/check-md-deadlinks.py --output-format list
```

**JSON** (for CI/CD):
```bash
python3 .github/scripts/check-md-deadlinks.py --output-format json
```

### Fail on deadlinks (for CI/CD)
```bash
python3 .github/scripts/check-md-deadlinks.py --fail-on-deadlinks
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
    python3 .github/scripts/check-md-deadlinks.py --fail-on-deadlinks
```

Without `--fail-on-deadlinks`, the step passes and each deadlink is reported as a GitHub warning annotation when running in GitHub Actions.

Or with JSON output for reporting:

```yaml
- name: Check markdown deadlinks
  id: deadlinks
  continue-on-error: true
  run: |
    python3 .github/scripts/check-md-deadlinks.py --output-format json > deadlinks.json
```

## Parameters

### `--repo-root` (path)
- Root directory to scan
- Default: `git rev-parse --show-toplevel` (current git repo root)
- Falls back to current directory if not in a git repo

### `--output-format` (choice)
- Output format for results
- Options: `table`, `list`, `json`
- Default: `table`

### `--fail-on-deadlinks` (flag)
- Exit with code 1 if any deadlinks found
- Useful for CI/CD pipelines
- Default: off (exit 0 regardless)

## Exit Codes

- **0** — Success (no deadlinks or `FailOnDeadlinks` not specified)
- **1** — Deadlinks found and `--fail-on-deadlinks` enabled
- **1** — No markdown files found

## What Gets Validated

✅ **Checked**:
- Relative file paths: `docs/guide.md`
- Subdirectory paths: `../workflows/ci.md`
- Paths with anchors: `file.md#section`

⏭️ **Skipped**:
- External URLs: `[text](https://github.com/...)`
- Mailto links: `[text](mailto:user@example.com)`
- Same-file anchors: `[text](#top)`
- Empty paths: `[text]()`

## Troubleshooting

### "No markdown files found"
- Check that markdown files exist in the repo
- Verify `--repo-root` parameter is correct

### False positives (valid links reported as dead)
- Check file path resolution
- Verify relative paths are correct
- Run with `--output-format list` to see the deadlinks with their targets

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
