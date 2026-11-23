"""Tests for the Kubescape chart scanner command."""

import subprocess
import tempfile
import unittest
from pathlib import Path

from helm_pipeline.core.commands import CommandRunner
from helm_pipeline.security.kubescape import KubescapeScanner
from helm_pipeline.security.reports import ERROR_REPORT, ScanReport


class RecordingRunner:
    """Record process invocations and return the configured exit code, standing in for subprocess.run."""

    def __init__(self, returncode=0):
        """Store the exit code to return for every invocation."""
        self.returncode = returncode
        self.calls = []

    def __call__(self, args, check=False, **kwargs):
        """Record the arguments and raise like subprocess.run when check is set and the exit code is non-zero."""
        self.calls.append(list(args))
        if check and self.returncode:
            raise subprocess.CalledProcessError(self.returncode, args)
        return subprocess.CompletedProcess(args, self.returncode)


class KubescapeScannerTest(unittest.TestCase):
    """Behavioral tests for the Kubescape scanner."""

    def test_scan_blocks_on_high_severity_and_writes_json_report(self):
        """Test that Kubescape runs with a high severity gate and writes its JSON report next to the chart reports."""
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory).resolve()
            runner = RecordingRunner()
            scanner = KubescapeScanner(CommandRunner(output, runner))
            scanner.scan(ScanReport(output), Path('manifest.yaml'), output)
        self.assertEqual(
            runner.calls,
            [[
                'kubescape', 'scan', 'manifest.yaml', '--format', 'json',
                '--output', str(output / 'kubescape.json'), '--severity-threshold', 'critical', '--keep-local',
            ]],
        )

    def test_scan_passes_chart_exception_file_when_present(self):
        """Test that a chart's Kubescape exception file is passed to Kubescape so its findings can be suppressed."""
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory).resolve()
            runner = RecordingRunner()
            scanner = KubescapeScanner(CommandRunner(output, runner))
            scanner.scan(ScanReport(output), Path('manifest.yaml'), output, 'exceptions.json')
        self.assertEqual(runner.calls[0][-2:], ['--exceptions', 'exceptions.json'])

    def test_findings_exit_code_is_not_a_scanner_failure(self):
        """Test that a Kubescape exit code of 1 for failed controls does not fail the scan or record an error."""
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory).resolve()
            scanner = KubescapeScanner(CommandRunner(output, RecordingRunner(returncode=1)))
            scanner.scan(ScanReport(output), Path('manifest.yaml'), output)
            recorded = (output / ERROR_REPORT).exists()
        self.assertFalse(recorded)

    def test_other_exit_codes_are_recorded_and_raised(self):
        """Test that a Kubescape failure other than findings is recorded in the scan report and raised."""
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory).resolve()
            scanner = KubescapeScanner(CommandRunner(output, RecordingRunner(returncode=2)))
            with self.assertRaises(subprocess.CalledProcessError):
                scanner.scan(ScanReport(output), Path('manifest.yaml'), output)
            errors = (output / ERROR_REPORT).read_text(encoding='utf-8')
        self.assertIn('kubescape', errors)


if __name__ == '__main__':
    unittest.main()
