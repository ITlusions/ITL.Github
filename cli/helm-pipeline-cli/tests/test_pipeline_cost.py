"""Tests for the total cost estimate written at the end of the pipeline."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from helm_pipeline.core.github import GitHubFiles
from helm_pipeline.security.pipeline_cost import PipelineCost
from case import test_case


class PipelineCostTest(unittest.TestCase):
    """Behavioral tests for the total pipeline cost estimate."""

    def setUp(self):
        """Create a step summary file for each test."""
        self.temporary = tempfile.TemporaryDirectory()
        self.step_summary = Path(self.temporary.name) / 'step-summary.md'
        self.environment = mock.patch.dict(os.environ, {'GITHUB_STEP_SUMMARY': str(self.step_summary)})
        self.environment.start()
        self.cost = PipelineCost(GitHubFiles())

    def tearDown(self):
        """Remove the temporary summary directory."""
        self.environment.stop()
        self.temporary.cleanup()

    def job(self, name, started, completed, conclusion):
        """Return a job dictionary in the shape of gh run view --json jobs."""
        return {'name': name, 'startedAt': started, 'completedAt': completed, 'conclusion': conclusion}

    @test_case('TC-COST-001', 'The total rounds each finished job up to whole minutes and ignores skipped or running jobs')
    def test_that_total_bills_each_finished_job_in_whole_minutes_and_ignores_skipped_and_running_jobs(self):
        """Test that the total rounds each finished job up to whole minutes and ignores skipped or running jobs."""
        jobs = [
            self.job('Chart a', '2026-11-23T10:00:00Z', '2026-11-23T10:01:21Z', 'success'),
            self.job('Chart b', '2026-11-23T10:00:00Z', '2026-11-23T10:01:10Z', 'success'),
            self.job('Chart c', None, None, 'skipped'),
            self.job('Pipeline cost estimate', '2026-11-23T10:02:00Z', None, None),
        ]

        self.cost.write(jobs)

        summary = self.step_summary.read_text(encoding='utf-8')
        self.assertIn('### Pipeline cost estimate', summary)
        self.assertIn('| Jobs billed | 2 |', summary)
        self.assertIn('| Billed minutes | 4 |', summary)
        self.assertIn('| Estimated cost | USD 0.0320 |', summary)


if __name__ == '__main__':
    unittest.main()
