"""Verify that every non-ignored chart contains the files that CI requires."""

import logging
from pathlib import Path

LOGGER = logging.getLogger(__name__)
# Files every non-ignored chart must contain, checked on every CI run.
REQUIRED_FILES = ('Chart.yaml', 'values.yaml', 'README.md', 'examples/minimal.yaml', 'examples/full.yaml')
# Minimum number of whitespace-separated words in a chart's README.md, markdown syntax included.
MIN_README_WORDS = 200


class RequirementsChecker:
    """Check each non-ignored chart for the required files."""

    def __init__(self, catalog):
        """Store the chart catalog.

        Args:
            catalog: A ChartCatalog instance.
        """
        self.catalog = catalog

    def missing(self, chart):
        """Return the required files that a chart directory lacks."""
        return [name for name in REQUIRED_FILES if not (self.catalog.root / chart / name).exists()]

    def problems(self, chart):
        """Return one message per requirement that a chart does not meet."""
        found = ['missing required file: ' + name for name in self.missing(chart)]
        readme = self.catalog.root / chart / 'README.md'
        if readme.is_file():
            words = len(readme.read_text(encoding='utf-8').split())
            if words < MIN_README_WORDS:
                found.append(f'README.md has {words} words, at least {MIN_README_WORDS} are required')
        return found

    def check(self):
        """Raise when any non-ignored chart lacks a required file or has a README that is too short."""
        failures = {}
        charts = self.catalog.chart_paths()
        self.catalog.log_ignored(charts)
        checked = [chart for chart in charts if not self.catalog.ignored(chart)]
        LOGGER.info('Checking %d chart(s) for %d required file(s) each (%s): %s',
                    len(checked), len(REQUIRED_FILES), ', '.join(REQUIRED_FILES), ', '.join(checked) or 'none')
        for chart in checked:
            problems = self.problems(chart)
            if problems:
                failures[chart] = problems
                LOGGER.error('%s: %s', chart, '; '.join(problems))
            else:
                LOGGER.info('%s: all requirements met', chart)
        if failures:
            LOGGER.error('%d of %d chart(s) do not meet the requirements', len(failures), len(checked))
            raise ValueError(f'{len(failures)} chart(s) do not meet the requirements')
        LOGGER.info('All %d non-ignored chart(s) meet the requirements', len(checked))
