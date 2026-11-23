"""Discover charts in the repository and read their metadata and ignore markers."""

import logging
from pathlib import Path

import yaml

LOGGER = logging.getLogger(__name__)
IGNORE_MARKER = '.ciignore'
# Charts that are not standalone Helm charts and are therefore not linted.
SKIPPED_LINT_CHARTS = ('spotinfo-applications',)


class ChartCatalog:
    """Find charts under the charts directory and expose their metadata and ignore state."""

    def __init__(self, root):
        """Store the repository root.

        Args:
            root: Repository root that contains the charts directory.
        """
        self.root = Path(root).resolve()

    def ignored(self, chart):
        """Return True when a chart directory contains the .ciignore marker file."""
        return (self.root / chart / IGNORE_MARKER).is_file()

    def log_ignored(self, charts):
        """Log each chart skipped by a .ciignore marker together with the marker's reason."""
        for chart in charts:
            if self.ignored(chart):
                reason = (self.root / chart / IGNORE_MARKER).read_text(encoding='utf-8').strip()
                LOGGER.info('Skipping %s: %s', chart, reason)

    def metadata(self, chart):
        """Return the parsed Chart.yaml of a chart directory, given as a path."""
        metadata = yaml.safe_load((chart / 'Chart.yaml').read_text(encoding='utf-8'))
        if not isinstance(metadata, dict):
            raise ValueError(f'{chart}: Chart.yaml must be a mapping')
        return metadata

    def chart_paths(self):
        """Return the repository path of every chart directory, sorted."""
        return sorted(f'charts/{path.parent.name}' for path in (self.root / 'charts').glob('*/Chart.yaml'))

    def all_charts(self):
        """Return every chart path that is not marked with a .ciignore file."""
        charts = self.chart_paths()
        self.log_ignored(charts)
        return [chart for chart in charts if not self.ignored(chart)]

    def validated_chart(self, name):
        """Return the repository path of a named chart, raising when the chart does not exist."""
        path = (self.root / 'charts' / name).resolve()
        if Path(name).name != name or path.parent != self.root / 'charts' or not (path / 'Chart.yaml').is_file():
            raise ValueError(f'Unknown chart: {name}')
        return f'charts/{name}'
