import tempfile
import unittest
from pathlib import Path

from helm_pipeline.charts.pipeline import ChartPipeline
from case import test_case


BASE_CHART = 'apiVersion: v2\nname: base\nversion: {version}\n'
DEPENDENT_CHART = (
    'apiVersion: v2\nname: app\nversion: 0.1.0\n'
    'dependencies:\n'
    '- name: base\n'
    '  version: 1.0.0\n'
    '  repository: file://../base\n'
)
DEPENDENT_LOCK = 'dependencies:\n- name: base\n  repository: file://../base\n  version: {version}\ndigest: sha256:abc\n'


class LockCheckTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.base = self.root / 'charts' / 'base'
        self.app = self.root / 'charts' / 'app'
        self.base.mkdir(parents=True)
        self.app.mkdir(parents=True)
        self.write_base('1.0.1')
        (self.app / 'Chart.yaml').write_text(DEPENDENT_CHART, encoding='utf-8')

    def tearDown(self):
        self.directory.cleanup()

    def write_base(self, version):
        (self.base / 'Chart.yaml').write_text(BASE_CHART.format(version=version), encoding='utf-8')

    def write_lock(self, version):
        (self.app / 'Chart.lock').write_text(DEPENDENT_LOCK.format(version=version), encoding='utf-8')

    @test_case('TC-LCK-001', 'A dependent whose Chart.lock pins an older local dependency version fails the check')
    def test_stale_lock_fails_the_check(self):
        """Test that a dependent whose Chart.lock pins an older local dependency version fails the check."""
        self.write_lock('1.0.0')
        with self.assertRaises(ValueError):
            ChartPipeline(self.root).check_locks('charts/app')

    @test_case('TC-LCK-002', 'A dependent whose Chart.lock pins the current local dependency version passes the check')
    def test_current_lock_passes_the_check(self):
        """Test that a dependent whose Chart.lock pins the current local dependency version passes the check."""
        self.write_lock('1.0.1')
        ChartPipeline(self.root).check_locks('charts/app')

    @test_case('TC-LCK-003', 'A dependent with local dependencies but no Chart.lock fails the check')
    def test_missing_lock_fails_the_check(self):
        """Test that a dependent with local dependencies but no Chart.lock fails the check."""
        with self.assertRaises(ValueError):
            ChartPipeline(self.root).check_locks('charts/app')

    @test_case('TC-LCK-004', 'A dependency from a remote repository is skipped because it cannot be verified offline')
    def test_remote_dependency_is_not_checked(self):
        """Test that a dependency from a remote repository is skipped because it cannot be verified offline."""
        (self.app / 'Chart.yaml').write_text(
            'apiVersion: v2\nname: app\nversion: 0.1.0\n'
            'dependencies:\n- name: base\n  version: 1.0.0\n  repository: https://charts.example.com\n',
            encoding='utf-8',
        )
        ChartPipeline(self.root).check_locks('charts/app')

    @test_case('TC-LCK-005', 'Omitting the chart checks every non-ignored chart and fails on a stale dependent')
    def test_all_charts_are_checked_when_no_chart_is_given(self):
        """Test that omitting the chart checks every non-ignored chart and fails on a stale dependent."""
        self.write_lock('1.0.0')
        with self.assertRaises(ValueError):
            ChartPipeline(self.root).check_locks()


if __name__ == '__main__':
    unittest.main()
