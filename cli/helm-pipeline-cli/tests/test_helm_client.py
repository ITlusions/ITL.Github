import subprocess
import tempfile
import unittest
from pathlib import Path

from helm_pipeline.charts.catalog import ChartCatalog
from helm_pipeline.charts.helm import HelmClient
from helm_pipeline.core.commands import CommandRunner
from case import test_case




class RecordingRunner:
    """Record executed commands and return the configured return codes in order."""

    def __init__(self, return_codes):
        """Store the return codes to hand out, one per command.

        Args:
            return_codes: Iterable of exit codes returned for successive commands.
        """
        self.return_codes = list(return_codes)
        self.calls = []

    def __call__(self, command, **_kwargs):
        """Record the command and return a completed process with the next exit code."""
        self.calls.append(command[:3])
        code = self.return_codes.pop(0) if self.return_codes else 0
        return subprocess.CompletedProcess(command, code, stdout='')


class HelmClientDependenciesTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.chart = self.root / 'charts' / 'example'
        self.chart.mkdir(parents=True)
        (self.chart / 'Chart.yaml').write_text('apiVersion: v2\nname: example\nversion: 0.1.0\n', encoding='utf-8')

    def client(self, return_codes):
        """Return a HelmClient whose commands are recorded instead of executed."""
        runner = RecordingRunner(return_codes)
        return HelmClient(CommandRunner(self.root, runner=runner), ChartCatalog(self.root)), runner

    @test_case('TC-HLM-001', 'A Chart.lock in sync with Chart.yaml is used directly with helm dependency build')
    def test_dependency_build_uses_lock_file_when_it_is_in_sync(self):
        """Test that a Chart.lock in sync with Chart.yaml is used directly with helm dependency build."""
        (self.chart / 'Chart.lock').write_text('dependencies: []\n', encoding='utf-8')
        client, runner = self.client([0])
        client.dependencies('charts/example')
        self.assertEqual(runner.calls, [['helm', 'dependency', 'build']])

    @test_case('TC-HLM-002', 'A Chart.lock out of sync with Chart.yaml is regenerated with helm dependency update instead of failing')
    def test_out_of_sync_lock_file_is_regenerated_with_dependency_update(self):
        """Test that a Chart.lock out of sync with Chart.yaml is regenerated with helm dependency update instead of failing."""
        (self.chart / 'Chart.lock').write_text('dependencies: []\n', encoding='utf-8')
        client, runner = self.client([1, 0])
        client.dependencies('charts/example')
        self.assertEqual(runner.calls, [['helm', 'dependency', 'build'], ['helm', 'dependency', 'update']])

    @test_case('TC-HLM-003', 'A chart without Chart.lock resolves its dependencies with helm dependency update')
    def test_missing_lock_file_falls_back_to_dependency_update(self):
        """Test that a chart without Chart.lock resolves its dependencies with helm dependency update."""
        client, runner = self.client([0])
        client.dependencies('charts/example')
        self.assertEqual(runner.calls, [['helm', 'dependency', 'update']])


if __name__ == '__main__':
    unittest.main()
