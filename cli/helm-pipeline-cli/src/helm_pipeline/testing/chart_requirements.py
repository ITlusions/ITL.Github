"""Basic chart requirement tests, run by the chart pipeline for every chart so charts need no test file of their own."""

import sys
import unittest
from pathlib import Path
from urllib.parse import urlparse

import yaml

from helm_pipeline.charts.catalog import ChartCatalog
from helm_pipeline.charts.requirements import MIN_README_WORDS, RequirementsChecker
from helm_pipeline.testing.case import test_case
from helm_pipeline.testing.chart import ChartTestCase



class ChartRequirementTests(ChartTestCase):
    """Basic requirements every chart must meet; the runner sets chart_dir and repository on a subclass."""

    chart_dir = None
    repository = None

    def setUp(self):
        """Skip the abstract base; only a subclass that sets chart_dir and repository runs the checks."""
        if self.chart_dir is None or self.repository is None:
            self.skipTest('abstract base: set chart_dir and repository on a subclass')

    @test_case('TC-CRQ-001', 'The chart contains every file the chart pipeline requires')
    def test_required_files_are_present(self):
        """Test that the chart contains every file the chart pipeline requires."""
        problems = RequirementsChecker(ChartCatalog(self.repository)).problems(f'charts/{self.chart_dir.name}')
        self.assertEqual([problem for problem in problems if problem.startswith('missing')], [])

    @test_case('TC-CRQ-002', 'The README.md of the chart has at least the minimum number of words')
    def test_readme_has_the_minimum_word_count(self):
        """Test that the README.md of the chart has at least the minimum number of words."""
        words = len((self.chart_dir / 'README.md').read_text(encoding='utf-8').split())
        self.assertGreaterEqual(words, MIN_README_WORDS)

    @test_case('TC-CRQ-003', 'Chart.yaml names the chart after its folder and sets a description, a version and an HTTPS icon')
    def test_chart_metadata_is_complete(self):
        """Test that Chart.yaml names the chart after its folder and sets a description, a version and an HTTPS icon."""
        metadata = yaml.safe_load((self.chart_dir / 'Chart.yaml').read_text(encoding='utf-8'))
        self.assertEqual(metadata.get('name'), self.chart_dir.name)
        for field in ('description', 'version'):
            self.assertTrue(str(metadata.get(field, '')).strip(), field)
        self.assertEqual(urlparse(str(metadata.get('icon', ''))).scheme, 'https')

    @test_case('TC-CRQ-004', 'The minimal and full examples are valid YAML mappings')
    def test_examples_are_mappings(self):
        """Test that the minimal and full examples are valid YAML mappings."""
        for name in ('minimal', 'full'):
            with self.subTest(example=name):
                values = yaml.safe_load((self.chart_dir / 'examples' / f'{name}.yaml').read_text(encoding='utf-8'))
                self.assertIsInstance(values, dict)


def run_chart_requirements(repository, chart_dir, stream=sys.stderr):
    """Run the basic requirement tests against one chart and return True when every test passes.

    Args:
        repository: Repository root that contains the charts directory.
        chart_dir: Chart folder, relative to the repository root or absolute.
        stream: Stream that receives the test report.
    """
    chart = Path(chart_dir)
    attributes = {'chart_dir': (chart if chart.is_absolute() else Path(repository) / chart).resolve(),
                  'repository': Path(repository).resolve()}
    case = type('ChartRequirements', (ChartRequirementTests,), attributes)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(case)
    return unittest.TextTestRunner(stream=stream).run(suite).wasSuccessful()
