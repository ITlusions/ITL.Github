import tempfile
import unittest
from pathlib import Path

from helm_pipeline.charts.catalog import ChartCatalog
from case import test_case
from helm_pipeline.charts.requirements import MIN_README_WORDS, RequirementsChecker


CHART_YAML = 'apiVersion: v2\nname: demo\nversion: 0.1.0\n'


def readme_with_words(count):
    """Return README text with exactly the given number of words."""
    return ' '.join(['word'] * count) + '\n'


class RequirementsTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.chart = self.root / 'charts' / 'demo'
        (self.chart / 'examples').mkdir(parents=True)
        (self.chart / 'Chart.yaml').write_text(CHART_YAML, encoding='utf-8')
        (self.chart / 'values.yaml').write_text('a: 1\n', encoding='utf-8')
        (self.chart / 'examples' / 'minimal.yaml').write_text('a: 1\n', encoding='utf-8')
        (self.chart / 'examples' / 'full.yaml').write_text('a: 1\n', encoding='utf-8')
        self.checker = RequirementsChecker(ChartCatalog(self.root))

    def tearDown(self):
        self.directory.cleanup()

    def write_readme(self, words):
        (self.chart / 'README.md').write_text(readme_with_words(words), encoding='utf-8')

    @test_case('TC-REQ-001', 'README.md with the minimum word count passes')
    def test_chart_with_long_enough_readme_passes(self):
        """Test that a chart with a README.md of at least the minimum word count meets the requirement."""
        self.write_readme(MIN_README_WORDS)
        self.checker.check()

    @test_case('TC-REQ-002', 'README.md one word below the minimum fails')
    def test_readme_one_word_short_fails(self):
        """Test that a README.md one word below the minimum fails the requirement."""
        self.write_readme(MIN_README_WORDS - 1)
        with self.assertRaisesRegex(ValueError, 'do not meet the requirements'):
            self.checker.check()
        self.assertIn(f'README.md has {MIN_README_WORDS - 1} words',
                      '; '.join(self.checker.problems('charts/demo')))

    @test_case('TC-REQ-003', 'Missing README.md at the chart root fails')
    def test_missing_readme_fails(self):
        """Test that a chart without a README.md at its root fails the requirement."""
        self.assertIn('missing required file: README.md', self.checker.problems('charts/demo'))

    @test_case('TC-REQ-004', 'README.md in a subfolder does not satisfy the requirement')
    def test_readme_in_a_subfolder_does_not_count(self):
        """Test that a README.md below the chart root, such as in docs/, does not satisfy the requirement."""
        (self.chart / 'docs').mkdir()
        (self.chart / 'docs' / 'README.md').write_text(readme_with_words(MIN_README_WORDS), encoding='utf-8')
        self.assertIn('missing required file: README.md', self.checker.problems('charts/demo'))

    @test_case('TC-REQ-005', 'Chart marked with .ciignore is excluded from the README rule')
    def test_ignored_chart_needs_no_readme(self):
        """Test that a chart marked with .ciignore is excluded from the README requirement."""
        (self.chart / '.ciignore').write_text('reason\n', encoding='utf-8')
        self.checker.check()


if __name__ == '__main__':
    unittest.main()
