"""Verify that every non-ignored chart contains the files that CI requires."""

import logging
from pathlib import Path

LOGGER = logging.getLogger(__name__)
# Files every non-ignored chart must contain, checked on every CI run.
REQUIRED_FILES = ('Chart.yaml', 'values.yaml', 'examples/minimal.yaml', 'examples/full.yaml')


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

    def check(self):
        """Raise when any non-ignored chart lacks a required file."""
        failures = {}
        charts = self.catalog.chart_paths()
        self.catalog.log_ignored(charts)
        checked = [chart for chart in charts if not self.catalog.ignored(chart)]
        LOGGER.info('Checking %d chart(s) for %d required file(s) each (%s): %s',
                    len(checked), len(REQUIRED_FILES), ', '.join(REQUIRED_FILES), ', '.join(checked) or 'none')
        for chart in checked:
            missing = self.missing(chart)
            if missing:
                failures[chart] = missing
                LOGGER.error('%s: missing required file(s): %s', chart, ', '.join(missing))
            else:
                LOGGER.info('%s: all required files present', chart)
        if failures:
            LOGGER.error('%d of %d chart(s) do not meet the requirements', len(failures), len(checked))
            raise ValueError(f'{len(failures)} chart(s) do not meet the requirements')
        LOGGER.info('All %d non-ignored chart(s) meet the requirements', len(checked))
