"""Tests for reading failed controls from a Kubescape JSON report."""

import json
import tempfile
import unittest
from pathlib import Path

from helm_pipeline.security.kubescape_report import KubescapeReport


class KubescapeReportTest(unittest.TestCase):
    """Behavioral tests for the Kubescape failing-controls reader."""

    def setUp(self):
        """Create a temporary directory for the report file."""
        self.temporary = tempfile.TemporaryDirectory()
        self.report = Path(self.temporary.name) / 'kubescape.json'

    def tearDown(self):
        """Remove the temporary directory."""
        self.temporary.cleanup()

    def test_that_only_failed_controls_are_returned_sorted_by_id(self):
        """Test that passed controls are skipped and failed controls are listed with name and failed resource count."""
        self.report.write_text(json.dumps({'summaryDetails': {'controls': {
            'C-0270': {'name': 'Resource limits', 'status': {'status': 'failed'},
                       'resourceCounters': {'failedResources': 2}},
            'C-0050': {'name': 'Resources CPU limit', 'status': {'status': 'failed'},
                       'resourceCounters': {'failedResources': 1}},
            'C-0001': {'name': 'Forbidden container', 'status': {'status': 'passed'},
                       'resourceCounters': {'failedResources': 0}},
        }}}), encoding='utf-8')

        controls = KubescapeReport(self.report).failing_controls()

        self.assertEqual([
            {'id': 'C-0050', 'name': 'Resources CPU limit', 'resources': 1},
            {'id': 'C-0270', 'name': 'Resource limits', 'resources': 2},
        ], controls)

    def test_that_missing_report_has_no_failing_controls(self):
        """Test that a missing report returns an empty list instead of failing the summary."""
        self.assertEqual([], KubescapeReport(self.report).failing_controls())


if __name__ == '__main__':
    unittest.main()
