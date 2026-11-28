"""Package charts into tarballs for distribution."""

import logging
from pathlib import Path

LOGGER = logging.getLogger(__name__)


class ChartPackager:
    """Build dependencies, lint, and package charts."""

    def __init__(self, catalog, helm):
        """Store the collaborators used for chart metadata and Helm commands.

        Args:
            catalog: A ChartCatalog instance.
            helm: A HelmClient instance.
        """
        self.catalog = catalog
        self.helm = helm

    def package(self, chart, destination):
        """Build dependencies, lint, and package one chart into the destination directory."""
        chart = Path(chart).resolve()
        destination = Path(destination).resolve()
        destination.mkdir(parents=True, exist_ok=True)
        self.helm.dependencies(chart)
        self.helm.lint(chart)
        self.helm.package(chart, destination)
        packages = sorted(destination.glob(f'{chart.name}-*.tgz'))
        if len(packages) != 1:
            raise ValueError(f'{chart.name}: expected exactly one chart package in {destination}')
        LOGGER.info('Packaged %s', packages[0].name)
        return packages[0]
