"""Tests for the audit that flags expired, expiring and stale exclusions."""

import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from helm_pipeline.core.github import GitHubFiles
from helm_pipeline.security.chart_exceptions import STATUS_ACTIVE, STATUS_EXPIRED
from helm_pipeline.security.exclusion_audit import KIND_EXPIRED, KIND_EXPIRING, KIND_STALE, ExclusionAudit
from helm_pipeline.security.misconfigurations import MisconfigurationReport

# AI generated code: GitHub Copilot Claude Haiku 5.5
TODAY = date(2026, 11, 23)


def exclusion(scanner, identifier, expires, status=STATUS_ACTIVE):
    """Return one exclusion row in the shape that ChartExceptions.exclusions() produces."""
    return {
        'scanner': scanner,
        'id': identifier,
        'detail': 'detail',
        'owner': 'Platform team',
        'expires': expires,
        'request': 'issue-1',
        'status': status,
    }


class ExclusionAuditTest(unittest.TestCase):
    """Behavioral tests for the exclusion audit."""

    def setUp(self):
        """Create a temporary directory with the scanner report paths and the audit under test."""
        self.temporary = tempfile.TemporaryDirectory()
        self.directory = Path(self.temporary.name)
        self.trivy_report = self.directory / 'config-unfiltered.json'
        self.kubescape_report = self.directory / 'kubescape.json'
        self.audit = ExclusionAudit(TODAY, MisconfigurationReport(GitHubFiles()))

    def tearDown(self):
        """Remove the temporary directory."""
        self.temporary.cleanup()

    def write_json(self, path, data):
        """Create a JSON file with the given content."""
        path.write_text(json.dumps(data), encoding='utf-8')

    def test_that_expired_exclusion_is_flagged_as_expired(self):
        """Test that an exclusion past its expiry date is reported as expired."""
        rows = [exclusion('trivy', 'KSV-0014', '2026-11-01', STATUS_EXPIRED)]

        issues = self.audit.audit(rows, self.trivy_report, self.kubescape_report)

        self.assertEqual([issue.kind for issue in issues], [KIND_EXPIRED])

    def test_that_exclusion_expiring_within_thirty_days_is_flagged(self):
        """Test that an active exclusion expiring within thirty days is reported, and one expiring later is not."""
        rows = [
            exclusion('trivy', 'KSV-0014', '2026-12-15'),
            exclusion('trivy', 'KSV-0041', '2027-06-01'),
        ]

        issues = self.audit.audit(rows, self.trivy_report, self.kubescape_report)

        self.assertEqual([(issue.kind, issue.identifier) for issue in issues], [(KIND_EXPIRING, 'KSV-0014')])
        self.assertIn('expires in 22 day(s)', issues[0].message)

    def test_that_trivy_exclusion_missing_from_unfiltered_report_is_stale(self):
        """Test that a Trivy exclusion whose misconfiguration no longer appears in the report is reported as stale."""
        self.write_json(self.trivy_report, {'Results': [{'Target': 'deploy.yaml', 'Misconfigurations': [
            {'ID': 'KSV-0041', 'Severity': 'HIGH', 'Title': 'Secret access'},
        ]}]})
        rows = [
            exclusion('trivy', 'KSV-0014', '2027-06-01'),
            exclusion('trivy', 'KSV-0041', '2027-06-01'),
        ]

        issues = self.audit.audit(rows, self.trivy_report, self.kubescape_report)

        self.assertEqual([(issue.kind, issue.identifier) for issue in issues], [(KIND_STALE, 'KSV-0014')])

    def test_that_kubescape_exclusion_for_a_control_that_was_not_evaluated_is_stale(self):
        """Test that a Kubescape exclusion naming a control that the scan did not evaluate is reported as stale."""
        self.write_json(self.kubescape_report, {'summaryDetails': {'controls': {
            'C-0009': {'name': 'Passing control', 'status': {'status': 'passed'}},
        }}})
        rows = [
            exclusion('kubescape', 'C-0004', '2027-06-01'),
            exclusion('kubescape', 'C-0009', '2027-06-01'),
        ]

        issues = self.audit.audit(rows, self.trivy_report, self.kubescape_report)

        self.assertEqual([(issue.kind, issue.identifier) for issue in issues], [(KIND_STALE, 'C-0004')])

    def test_that_stale_check_is_skipped_when_the_scanner_report_is_missing(self):
        """Test that no stale issue is raised when the scanner report does not exist to compare against."""
        rows = [
            exclusion('trivy', 'KSV-0014', '2027-06-01'),
            exclusion('kubescape', 'C-0004', '2027-06-01'),
        ]

        issues = self.audit.audit(rows, self.trivy_report, self.kubescape_report)

        self.assertEqual(issues, [])


if __name__ == '__main__':
    unittest.main()
