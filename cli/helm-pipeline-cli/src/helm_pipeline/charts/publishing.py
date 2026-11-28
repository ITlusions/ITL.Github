"""Publish charts to an OCI registry after verifying that the version is new."""

import logging
import tempfile
from pathlib import Path

LOGGER = logging.getLogger(__name__)


class ChartPublisher:
    """Check chart versions against a registry and push packaged charts to it."""

    def __init__(self, catalog, helm):
        """Store the collaborators used for chart metadata and Helm commands.

        Args:
            catalog: A ChartCatalog instance.
            helm: A HelmClient instance.
        """
        self.catalog = catalog
        self.helm = helm

    def check_version(self, chart, registry=None):
        """Check that the chart declares a version and, when a registry is given, that it is not published yet."""
        chart = Path(chart).resolve()
        version = str(self.catalog.metadata(chart).get('version', ''))
        if not version:
            raise ValueError(f'{chart.name}: chart version is missing')
        if registry:
            result = self.helm.show_chart(registry, chart.name, version)
            if result.returncode == 0:
                raise ValueError(f'{chart.name} {version} already exists in the registry')
            error = (result.stderr or '').lower()
            reference = f'{registry}/charts/{chart.name}:{version}'.lower()
            if not any(marker in error for marker in ('manifest unknown', '404 not found', f'{reference}: not found')):
                raise RuntimeError(f'Registry check failed: {result.stderr}')
            LOGGER.info('%s %s is not published to %s yet', chart.name, version, registry)

    def publish(self, chart, registry, username, password):
        """Log in, verify the version is new, package the chart, and push it to the registry."""
        if not registry or not username or not password:
            raise ValueError('Registry, username and password are required')
        chart = Path(chart).resolve()
        self.helm.registry_login(registry, username, password)
        self.check_version(chart, registry=registry)
        self.helm.add_repositories()
        self.helm.dependencies(chart)
        with tempfile.TemporaryDirectory() as directory:
            self.helm.package(chart, directory)
            packages = list(Path(directory).glob('*.tgz'))
            if len(packages) != 1:
                raise ValueError(f'{chart.name}: expected exactly one chart package')
            LOGGER.info('Pushing %s to %s', packages[0].name, registry)
            self.helm.push(packages[0], registry)
