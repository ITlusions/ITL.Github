"""Tests for the plain-language Kubescape failure log in the security CLI."""

import json
import logging
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

from helm_pipeline.cli.security_cli import SecurityCli
from helm_pipeline.security.pipeline import SecurityPipeline
from helm_pipeline.security.summary import KUBESCAPE_REPORT

# AI generated code: GitHub Copilot Claude Haiku 5.5


class SecurityCliFailureLogTest(unittest.TestCase):
    """Behavioral tests for logging failed Kubescape controls after a chart scan."""

    def setUp(self):
        """Create a temporary repository root with a chart report directory."""
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.pipeline = SecurityPipeline(self.root)
        self.report_dir = self.root / 'dist' / 'security' / 'spotinfo-api-gateway'
        self.report_dir.mkdir(parents=True)

    def tearDown(self):
        """Remove the temporary repository root."""
        self.temporary.cleanup()

    def write_report(self, controls):
        """Write a Kubescape JSON report for the chart with the given controls."""
        (self.report_dir / KUBESCAPE_REPORT).write_text(
            json.dumps({'summaryDetails': {'controls': controls}}), encoding='utf-8')

    def test_that_each_failed_control_is_logged_in_plain_words(self):
        """Test that every failed control is logged with its ID, name and failed resource count."""
        self.write_report({
            'C-0270': {'name': 'Resource limits', 'status': {'status': 'failed'},
                       'ResourceCounters': {'failedResources': 2}},
            'C-0001': {'name': 'Forbidden container', 'status': {'status': 'passed'},
                       'ResourceCounters': {'failedResources': 0}},
        })
        args = Namespace(command='chart', chart='charts/spotinfo-api-gateway')

        with self.assertLogs(level=logging.ERROR) as logs:
            SecurityCli().log_failing_controls(args, self.pipeline)

        self.assertEqual(
            ['Kubescape control C-0270 (Resource limits) failed on 2 resource(s)'],
            [record.getMessage() for record in logs.records])

    def test_that_non_chart_commands_log_no_controls(self):
        """Test that scans other than a chart scan do not read a Kubescape report."""
        self.write_report({
            'C-0270': {'name': 'Resource limits', 'status': 'failed',
                       'ResourceCounters': {'failedResources': 1}},
        })
        args = Namespace(command='repository', chart=None)

        with self.assertNoLogs(level=logging.ERROR):
            SecurityCli().log_failing_controls(args, self.pipeline)

    def test_that_missing_report_logs_no_controls(self):
        """Test that a chart scan without a Kubescape report logs nothing and does not raise."""
        args = Namespace(command='chart', chart='charts/spotinfo-api-gateway')

        with self.assertNoLogs(level=logging.ERROR):
            SecurityCli().log_failing_controls(args, self.pipeline)


if __name__ == '__main__':
    unittest.main()
