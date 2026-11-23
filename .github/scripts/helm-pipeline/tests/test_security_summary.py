"""Tests for the job summaries written after each security-scan step."""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from helm_pipeline.core.github import GitHubFiles
from helm_pipeline.security.reports import ERROR_REPORT
from helm_pipeline.security.summary import SecuritySummary


class SecuritySummaryTest(unittest.TestCase):
    """Behavioral tests for the security job summary."""

    def setUp(self):
        """Create a repository root and a step summary file for each test."""
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.step_summary = self.root / 'step-summary.md'
        self.environment = mock.patch.dict(os.environ, {'GITHUB_STEP_SUMMARY': str(self.step_summary)})
        self.environment.start()
        self.summary = SecuritySummary(GitHubFiles(), self.root)

    def tearDown(self):
        """Remove the temporary repository root."""
        self.environment.stop()
        self.temporary.cleanup()

    def read_summary(self):
        """Return everything written to the job summary so far."""
        return self.step_summary.read_text(encoding='utf-8') if self.step_summary.is_file() else ''

    def write_json(self, path, data):
        """Create a JSON file, including its parent directories."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data), encoding='utf-8')

    def test_that_chart_summary_reports_passed_and_skipped_scanners(self):
        """Test that a chart summary shows which scanners ran and passed, and which were skipped."""
        output = self.root / 'dist' / 'security' / 'my-chart'
        self.write_json(output / 'config.json', {'Results': []})
        self.write_json(output / 'images.json', ['nginx:1.27', 'redis:7'])

        self.summary.write('chart', 'charts/my-chart')

        summary = self.read_summary()
        self.assertIn('### Chart security: my-chart', summary)
        self.assertIn('| Trivy misconfigurations | passed | - |', summary)
        self.assertIn('| Kubescape | skipped | - |', summary)
        self.assertIn('| Trivy image scans | passed | 2 image(s) |', summary)

    def test_that_chart_summary_reports_failed_scanner_and_lists_errors(self):
        """Test that a failed scanner is marked as failed and its error appears in the summary."""
        output = self.root / 'dist' / 'security' / 'my-chart'
        self.write_json(output / ERROR_REPORT, [{'scanner': 'kubescape', 'message': 'exit code 1'}])

        self.summary.write('chart', 'my-chart')

        summary = self.read_summary()
        self.assertIn('| Kubescape | failed | - |', summary)
        self.assertIn('### Scanner errors', summary)
        self.assertIn('| kubescape | exit code 1 |', summary)

    def test_that_chart_summary_lists_failed_kubescape_controls(self):
        """Test that the chart summary names each failed Kubescape control with its failed resource count."""
        output = self.root / 'dist' / 'security' / 'my-chart'
        self.write_json(output / 'kubescape.json', {'summaryDetails': {'controls': {
            'C-0270': {'name': 'Resource limits', 'status': {'status': 'failed'},
                       'ResourceCounters': {'failedResources': 2}}}}})

        self.summary.write('chart', 'my-chart')

        summary = self.read_summary()
        self.assertIn('### Kubescape failing controls', summary)
        self.assertIn('| C-0270 | Resource limits | 2 |', summary)

    def test_that_secret_summary_lists_findings_without_secret_values(self):
        """Test that gitleaks findings appear with file and rule, and the scan exit error is hidden."""
        output = self.root / 'dist' / 'security' / 'repository'
        self.write_json(output / 'gitleaks.json', [
            {'File': 'values.yaml', 'StartLine': 12, 'RuleID': 'generic-api-key', 'Description': 'API key',
             'Secret': 'REDACTED'}])
        self.write_json(output / ERROR_REPORT, [{'scanner': 'gitleaks', 'message': 'exit status 1'}])

        self.summary.write('secrets')

        summary = self.read_summary()
        self.assertIn('| gitleaks | findings | 1 finding(s) |', summary)
        self.assertIn('| values.yaml | 12 | generic-api-key | API key |', summary)
        self.assertNotIn('REDACTED', summary)
        self.assertNotIn('exit status 1', summary)

    def test_that_dependency_summary_lists_each_vulnerability_with_fix_versions(self):
        """Test that each pip-audit vulnerability is listed with its package, version and fix versions."""
        output = self.root / 'dist' / 'security' / 'repository'
        self.write_json(output / 'pip-audit.json', {'dependencies': [
            {'name': 'requests', 'version': '2.0.0', 'vulns': [{'id': 'PYSEC-1', 'fix_versions': ['2.31.0']}]},
            {'name': 'urllib3', 'version': '1.0.0', 'vulns': []}]})

        self.summary.write('dependencies')

        summary = self.read_summary()
        self.assertIn('| pip-audit | findings | 1 vulnerability(ies) |', summary)
        self.assertIn('| requests | 2.0.0 | PYSEC-1 | 2.31.0 |', summary)
        self.assertNotIn('urllib3', summary)

    def write_layout_fixture(self):
        """Create a chart with one failing control, one active and one expired exclusion."""
        output = self.root / 'dist' / 'security' / 'my-chart'
        self.write_json(output / 'kubescape.json', {'summaryDetails': {'controls': {
            'C-0270': {'name': 'Resource limits', 'status': {'status': 'failed'},
                       'ResourceCounters': {'failedResources': 2}}}}})
        exceptions = self.root / 'charts' / 'my-chart' / 'exceptions.yaml'
        exceptions.parent.mkdir(parents=True, exist_ok=True)
        exceptions.write_text(
            'kubescape:\n'
            '  - name: Allowed root\n'
            '    posturePolicies:\n'
            '      - controlID: C-0007\n'
            '    owner: team-a\n'
            '    expires: 2099-01-01\n'
            '    request: REQ-1\n'
            'trivy:\n'
            '  misconfig:\n'
            '    - id: KSV-0014\n'
            '      statement: Old reason\n'
            '      owner: team-b\n'
            '      expires: 2000-01-01\n'
            '      request: REQ-2\n', encoding='utf-8')

    def summary_for(self, layout):
        """Return a summary writer that uses the given layout."""
        return SecuritySummary(GitHubFiles(), self.root, layout)

    def test_that_classic_layout_is_the_default_and_lists_only_failing_controls(self):
        """Test that the default layout keeps the failing controls table and does not list exclusions."""
        self.write_layout_fixture()

        self.summary.write('chart', 'my-chart')

        summary = self.read_summary()
        self.assertIn('### Kubescape failing controls', summary)
        self.assertIn('| C-0270 | Resource limits | 2 |', summary)
        self.assertNotIn('### Findings', summary)

    def test_that_flat_layout_lists_every_finding_with_status_owner_and_request(self):
        """Test that the flat layout shows blocking, excluded and expired findings in one table."""
        self.write_layout_fixture()

        self.summary_for('flat').write('chart', 'my-chart')

        summary = self.read_summary()
        self.assertIn('### Findings: my-chart', summary)
        self.assertIn('| kubescape | C-0270 | Resource limits | 2 | blocking | - | - | - |', summary)
        self.assertIn('| kubescape | C-0007 | Allowed root | - | excluded | team-a | 2099-01-01 | REQ-1 |', summary)
        self.assertIn('| trivy | KSV-0014 | Old reason | - | expired | team-b | 2000-01-01 | REQ-2 |', summary)

    def test_that_sections_layout_separates_blocking_excluded_and_expired_findings(self):
        """Test that the sections layout writes one table per status."""
        self.write_layout_fixture()

        self.summary_for('sections').write('chart', 'my-chart')

        summary = self.read_summary()
        self.assertIn('### Blocking findings: my-chart', summary)
        self.assertIn('### Excluded findings: my-chart', summary)
        self.assertIn('### Expired exclusions: my-chart', summary)
        self.assertIn('| kubescape | C-0007 | Allowed root | - | excluded | team-a | 2099-01-01 | REQ-1 |', summary)

    def test_that_counts_layout_shows_how_many_findings_have_each_status(self):
        """Test that the counts layout shows one count per status and lists only the blocking findings."""
        self.write_layout_fixture()

        self.summary_for('counts').write('chart', 'my-chart')

        summary = self.read_summary()
        self.assertIn('| blocking | 1 |', summary)
        self.assertIn('| excluded | 1 |', summary)
        self.assertIn('| expired | 1 |', summary)
        self.assertIn('### Blocking findings: my-chart', summary)
        self.assertNotIn('| C-0007 |', summary)

    def test_that_expiry_layout_sorts_exclusions_by_expiry_date_with_days_left(self):
        """Test that the expiry layout lists the earliest expiring exclusion first and counts days left."""
        self.write_layout_fixture()

        self.summary_for('expiry').write('chart', 'my-chart')

        summary = self.read_summary()
        self.assertIn('### Exclusions by expiry: my-chart', summary)
        self.assertIn('| 2000-01-01 |', summary)
        self.assertLess(summary.index('| 2000-01-01 |'), summary.index('| 2099-01-01 |'))
        self.assertIn('| Expires | Days left | Scanner | ID | Owner | Request | Status |', summary)

    def test_that_unknown_layout_name_is_rejected(self):
        """Test that a layout name that is not one of the five layouts fails before anything is written."""
        with self.assertRaises(ValueError):
            SecuritySummary(GitHubFiles(), self.root, 'fancy')

    def test_that_steps_without_summary_write_nothing(self):
        """Test that the setup and repository steps do not write a job summary."""
        self.summary.write('setup-tools')

        self.assertEqual('', self.read_summary())


if __name__ == '__main__':
    unittest.main()
