"""Verify that each chart's Chart.lock pins the current version of its local chart dependencies."""

import logging
from pathlib import Path

import yaml

LOGGER = logging.getLogger(__name__)

LOCAL_REPOSITORY_PREFIX = 'file://'


class LockChecker:
    """Check that Chart.lock pins the current version of every local chart dependency."""

    def __init__(self, catalog):
        """Store the chart catalog.

        Args:
            catalog: A ChartCatalog instance.
        """
        self.catalog = catalog

    def stale_problems(self, chart):
        """Return one message per local dependency whose locked version differs from its current version.

        Args:
            chart: Repository path of the chart, such as charts/demo.
        """
        directory = self.catalog.root / chart
        declared = self.catalog.metadata(directory).get('dependencies') or []
        locked = self.locked_versions(directory)
        problems = []
        for dependency in declared:
            repository = str(dependency.get('repository', ''))
            if not repository.startswith(LOCAL_REPOSITORY_PREFIX):
                continue
            name = dependency['name']
            local = (directory / repository[len(LOCAL_REPOSITORY_PREFIX):]).resolve()
            current = str(self.catalog.metadata(local)['version'])
            pinned = locked.get(name)
            if pinned != current:
                problems.append(f'{name}: Chart.lock pins {pinned or "no version"}, current version is {current}')
        return problems

    def locked_versions(self, directory):
        """Return a mapping of dependency name to locked version from a chart's Chart.lock, empty when absent."""
        lock = directory / 'Chart.lock'
        if not lock.is_file():
            return {}
        content = yaml.safe_load(lock.read_text(encoding='utf-8')) or {}
        return {entry['name']: str(entry['version']) for entry in content.get('dependencies') or []}

    def check(self, chart=None):
        """Raise when the Chart.lock of one chart, or of every non-ignored chart, is stale.

        Args:
            chart: Repository path of a single chart to check, or None to check every non-ignored chart.
        """
        charts = [chart] if chart else self.catalog.all_charts()
        failures = {}
        for name in charts:
            problems = self.stale_problems(name)
            for problem in problems:
                LOGGER.error('%s: %s', name, problem)
            if problems:
                failures[name] = problems
        if failures:
            LOGGER.error('Run helm dependency update and bump the version of: %s', ', '.join(failures))
            raise ValueError(f'{len(failures)} chart(s) have a stale Chart.lock')
        LOGGER.info('Chart.lock is current for %d chart(s)', len(charts))
