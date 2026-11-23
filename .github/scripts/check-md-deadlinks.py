#!/usr/bin/env python3
"""Scan markdown files for deadlinks (broken relative file references).

Recursively scans all ``*.md`` files below the repository root and checks that
relative link targets exist. External URLs and pure anchors are skipped. When
running inside GitHub Actions, each deadlink is also emitted as a warning
annotation.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
EXTERNAL_PATTERN = re.compile(r"^(https?://|mailto:)")
OUTPUT_FORMATS = ("table", "list", "json")


@dataclass(frozen=True)
class Deadlink:
    """A link whose relative target does not exist."""

    file: str
    line: int
    link_text: str
    link_url: str
    resolved_to: str
    status: str = "DEAD"


@dataclass
class ScanResult:
    """Aggregated counts and deadlinks for one scan."""

    valid: int = 0
    skipped: int = 0
    deadlinks: list[Deadlink] = field(default_factory=list)

    @property
    def total(self) -> int:
        """Return the number of links seen, regardless of status."""
        return self.valid + self.skipped + len(self.deadlinks)


class DeadlinkScanner:
    """Finds markdown files and validates their relative links."""

    def __init__(self, repo_root: Path) -> None:
        """Create a scanner rooted at the given directory.

        Args:
            repo_root: Directory to scan recursively.
        """
        self.repo_root = repo_root

    def markdown_files(self) -> list[Path]:
        """Return all markdown files below the repository root, sorted.

        Returns:
            Sorted list of ``*.md`` file paths.
        """
        return sorted(path for path in self.repo_root.rglob("*.md") if path.is_file())

    def scan(self, files: list[Path]) -> ScanResult:
        """Validate every link in the given markdown files.

        Args:
            files: Markdown files to scan.

        Returns:
            Counts of valid and skipped links, plus all deadlinks found.
        """
        result = ScanResult()
        for md_file in files:
            text = md_file.read_text(encoding="utf-8", errors="replace")
            for line_number, line in enumerate(text.splitlines(), start=1):
                for match in LINK_PATTERN.finditer(line):
                    self._check_link(md_file, line_number, match.group(1), match.group(2), result)
        return result

    def _check_link(
        self,
        md_file: Path,
        line_number: int,
        link_text: str,
        link_url: str,
        result: ScanResult,
    ) -> None:
        """Classify a single link and record it in the result.

        Args:
            md_file: Markdown file containing the link.
            line_number: One-based line number of the link.
            link_text: Text between the square brackets.
            link_url: Target between the parentheses.
            result: Accumulator updated in place.
        """
        if EXTERNAL_PATTERN.match(link_url):
            result.skipped += 1
            return

        link_path = link_url.split("#", 1)[0]
        if not link_path.strip():
            result.skipped += 1
            return

        resolved = Path(os.path.abspath(md_file.parent / link_path))
        if resolved.exists():
            result.valid += 1
            return

        result.deadlinks.append(
            Deadlink(
                file=md_file.relative_to(self.repo_root).as_posix(),
                line=line_number,
                link_text=link_text,
                link_url=link_url,
                resolved_to=str(resolved),
            )
        )
        if os.environ.get("GITHUB_ACTIONS") == "true":
            print(f"::warning file={md_file.relative_to(self.repo_root).as_posix()},line={line_number}::Deadlink: {link_url}")


class DeadlinkReporter:
    """Prints scan results in the requested format."""

    def __init__(self, repo_root: Path, output_format: str) -> None:
        """Create a reporter.

        Args:
            repo_root: Repository root, included in JSON output.
            output_format: One of ``table``, ``list`` or ``json``.
        """
        self.repo_root = repo_root
        self.output_format = output_format

    def report(self, result: ScanResult) -> None:
        """Print the summary and, when deadlinks exist, the deadlinks.

        Args:
            result: Scan result to print.
        """
        print("")
        print("Summary")
        print(f"  Total links found: {result.total}")
        print(f"  Valid: {result.valid}")
        print(f"  Skipped (external/anchor): {result.skipped}")
        print(f"  Deadlinks: {len(result.deadlinks)}")
        print("")

        if not result.deadlinks:
            print("No deadlinks found!")
            return

        if self.output_format == "table":
            self._print_table(result.deadlinks)
        elif self.output_format == "list":
            self._print_list(result.deadlinks)
        else:
            self._print_json(result)
        print("")

    def _print_table(self, deadlinks: list[Deadlink]) -> None:
        """Print deadlinks as a fixed-width table.

        Args:
            deadlinks: Deadlinks to print.
        """
        print("Deadlinks Found:")
        print("")
        rows = [("File", "Line", "Link", "Target")]
        rows += [(d.file, str(d.line), d.link_text, d.link_url) for d in deadlinks]
        widths = [max(len(row[i]) for row in rows) for i in range(4)]
        for row in rows:
            print("  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)).rstrip())

    def _print_list(self, deadlinks: list[Deadlink]) -> None:
        """Print one deadlink per line as ``file:line - [text](target)``.

        Args:
            deadlinks: Deadlinks to print.
        """
        print("Deadlinks Found:")
        print("")
        for d in deadlinks:
            print(f"{d.file}:{d.line} - [{d.link_text}]({d.link_url})")

    def _print_json(self, result: ScanResult) -> None:
        """Print the full result as JSON.

        Args:
            result: Scan result to serialize.
        """
        payload = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "repoRoot": str(self.repo_root),
            "summary": {
                "totalLinks": result.total,
                "validLinks": result.valid,
                "skippedLinks": result.skipped,
                "deadlinks": len(result.deadlinks),
            },
            "deadlinks": [
                {
                    "File": d.file,
                    "Line": d.line,
                    "LinkText": d.link_text,
                    "LinkUrl": d.link_url,
                    "ResolvedTo": d.resolved_to,
                    "Status": d.status,
                }
                for d in result.deadlinks
            ],
        }
        print(json.dumps(payload, indent=2))


def default_repo_root() -> Path:
    """Return the git top-level directory, or the current directory outside git.

    Returns:
        Repository root path.
    """
    completed = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode == 0 and completed.stdout.strip():
        return Path(completed.stdout.strip())
    return Path.cwd()


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Argument list, or None to read from ``sys.argv``.

    Returns:
        Parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Scan markdown files for deadlinks.")
    parser.add_argument("--repo-root", type=Path, default=None, help="Root directory to scan. Defaults to git root or cwd.")
    parser.add_argument("--output-format", choices=OUTPUT_FORMATS, default="table", help="Output format.")
    parser.add_argument("--fail-on-deadlinks", action="store_true", help="Exit with code 1 if deadlinks are found.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run the deadlink scan and report results.

    Args:
        argv: Argument list, or None to read from ``sys.argv``.

    Returns:
        Process exit code: 0 on success, 1 when no markdown files exist or
        deadlinks are found with ``--fail-on-deadlinks``.
    """
    args = parse_args(argv)
    repo_root = (args.repo_root or default_repo_root()).resolve()

    scanner = DeadlinkScanner(repo_root)
    files = scanner.markdown_files()
    if not files:
        print(f"No markdown files found in {repo_root}", file=sys.stderr)
        return 1

    print(f"Scanning {len(files)} markdown files for deadlinks...")
    result = scanner.scan(files)
    DeadlinkReporter(repo_root, args.output_format).report(result)

    if result.deadlinks:
        if args.fail_on_deadlinks:
            print("Pipeline would fail due to deadlinks")
            return 1
        print(f"{len(result.deadlinks)} deadlink(s) reported as warnings")
    return 0


if __name__ == "__main__":
    sys.exit(main())
