"""Tests for the Trivy image vulnerability report."""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from helm_pipeline.core.commands import CommandRunner
from helm_pipeline.core.github import GitHubFiles
from helm_pipeline.security.trivy import VULNERABILITY_REPORT, TrivyScanner
from case import test_case


IMAGE = 'registry.example.com/team/api:2.4.1'


class SilentRunner:
    """Accept every invocation without writing output, standing in for subprocess.run."""

    def __call__(self, args, check=False, **kwargs):
        """Return a successful process result."""
        return None


def trivy_report(vulnerabilities):
    """Build a minimal Trivy image JSON report containing the given vulnerabilities."""
    return {'Results': [{'Target': IMAGE, 'Vulnerabilities': vulnerabilities}]}


class TrivyVulnerabilityReportTest(unittest.TestCase):
    """Behavioral tests for the CVE details of Trivy image scans."""

    @test_case('TC-TRV-001', 'Every CRITICAL and HIGH CVE is written with its package, versions and title, critical first')
    def test_report_lists_critical_before_high_cves_with_details(self):
        """Test that every CRITICAL and HIGH CVE is written with its package, versions and title, critical first."""
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory).resolve()
            scanner = TrivyScanner(CommandRunner(output, SilentRunner()), GitHubFiles())
            identifier = scanner.identifier(IMAGE)
            (output / f'image-{identifier}.json').write_text(json.dumps(trivy_report([{
                'VulnerabilityID': 'CVE-2026-0001', 'Severity': 'CRITICAL', 'PkgName': 'openssl',
                'InstalledVersion': '3.0.1', 'FixedVersion': '3.0.2', 'Title': 'Buffer overflow',
            }])), encoding='utf-8')
            (output / f'image-high-{identifier}.json').write_text(json.dumps(trivy_report([{
                'VulnerabilityID': 'CVE-2026-0002', 'Severity': 'HIGH', 'PkgName': 'zlib',
                'InstalledVersion': '1.2.11', 'FixedVersion': '1.2.13', 'Title': 'Memory leak',
            }])), encoding='utf-8')
            scanner.vulnerability_report('api', output, [IMAGE])
            findings = json.loads((output / VULNERABILITY_REPORT).read_text(encoding='utf-8'))
        self.assertEqual([item['id'] for item in findings], ['CVE-2026-0001', 'CVE-2026-0002'])
        self.assertEqual(findings[0]['package'], 'openssl')
        self.assertEqual(findings[0]['installed'], '3.0.1')
        self.assertEqual(findings[0]['fixed'], '3.0.2')
        self.assertEqual(findings[1]['title'], 'Memory leak')

    @test_case('TC-TRV-002', 'The CVE table with severity, CVE, package and fixed version appears in the job summary')
    def test_cve_table_is_added_to_job_summary(self):
        """Test that the CVE table with severity, CVE, package and fixed version appears in the job summary."""
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory).resolve()
            summary = output / 'summary.md'
            scanner = TrivyScanner(CommandRunner(output, SilentRunner()), GitHubFiles())
            (output / f'image-high-{scanner.identifier(IMAGE)}.json').write_text(json.dumps(trivy_report([{
                'VulnerabilityID': 'CVE-2026-0002', 'Severity': 'HIGH', 'PkgName': 'zlib',
                'InstalledVersion': '1.2.11', 'FixedVersion': '1.2.13', 'Title': 'Memory leak',
            }])), encoding='utf-8')
            with mock.patch.dict(os.environ, {'GITHUB_STEP_SUMMARY': str(summary)}):
                scanner.vulnerability_report('api', output, [IMAGE])
            text = summary.read_text(encoding='utf-8')
        self.assertIn('### Image vulnerabilities: api', text)
        self.assertIn('| HIGH | ' + IMAGE + ' | CVE-2026-0002 | zlib | 1.2.11 | 1.2.13 | Memory leak |', text)

    @test_case('TC-TRV-003', 'An image without scan output yields an empty CVE report and no job summary table')
    def test_missing_reports_produce_empty_report_and_no_table(self):
        """Test that an image without scan output yields an empty CVE report and no job summary table."""
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory).resolve()
            summary = output / 'summary.md'
            scanner = TrivyScanner(CommandRunner(output, SilentRunner()), GitHubFiles())
            with mock.patch.dict(os.environ, {'GITHUB_STEP_SUMMARY': str(summary)}):
                scanner.vulnerability_report('api', output, [IMAGE])
            findings = json.loads((output / VULNERABILITY_REPORT).read_text(encoding='utf-8'))
            summary_exists = summary.exists()
        self.assertEqual(findings, [])
        self.assertFalse(summary_exists)


if __name__ == '__main__':
    unittest.main()
