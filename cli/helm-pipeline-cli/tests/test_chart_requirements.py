import io
import tempfile
import unittest
from pathlib import Path

from helm_pipeline.testing.chart_requirements import run_chart_requirements
from helm_pipeline.testing.case import test_case

CHART_YAML = 'apiVersion: v2\nname: demo\ndescription: Demo chart\nversion: 0.1.0\nicon: https://example.com/icon.svg\n'


class ChartRequirementRunnerTest(unittest.TestCase):
    """Behavioral tests for running the shared chart requirement tests against one chart."""

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.chart = self.root / 'charts' / 'demo'
        (self.chart / 'examples').mkdir(parents=True)
        (self.chart / 'Chart.yaml').write_text(CHART_YAML, encoding='utf-8')
        (self.chart / 'values.yaml').write_text('a: 1\n', encoding='utf-8')
        (self.chart / 'examples' / 'minimal.yaml').write_text('a: 1\n', encoding='utf-8')
        (self.chart / 'examples' / 'full.yaml').write_text('a: 1\n', encoding='utf-8')
        (self.chart / 'README.md').write_text(' '.join(['word'] * 200) + '\n', encoding='utf-8')

    def tearDown(self):
        self.directory.cleanup()

    @test_case('TC-CRR-001', 'A chart meeting every shared requirement passes the runner')
    def test_complete_chart_passes(self):
        """Test that a chart meeting every shared requirement passes the runner."""
        self.assertTrue(run_chart_requirements(self.root, 'charts/demo', io.StringIO()))

    @test_case('TC-CRR-002', 'A chart whose README has too few words fails the runner')
    def test_short_readme_fails(self):
        """Test that a chart whose README has too few words fails the runner."""
        (self.chart / 'README.md').write_text('too short\n', encoding='utf-8')
        self.assertFalse(run_chart_requirements(self.root, 'charts/demo', io.StringIO()))


if __name__ == '__main__':
    unittest.main()
