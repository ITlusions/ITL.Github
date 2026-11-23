"""Lint and validate charts: dependency builds, linting, unit tests, render checks, and schema validation."""

import logging
import sys
from pathlib import Path

import yaml

from helm_pipeline.charts.catalog import SKIPPED_LINT_CHARTS

LOGGER = logging.getLogger(__name__)
CRD_SCHEMA_LOCATION = (
    'https://raw.githubusercontent.com/datreeio/CRDs-catalog/main/'
    '{{.Group}}/{{.ResourceKind}}_{{.ResourceAPIVersion}}.json'
)


class ChartValidator:
    """Run the lint, unit-test, render, and kubeconform checks for charts."""

    def __init__(self, commands, catalog, helm):
        """Store the collaborators used to run commands, read chart metadata, and invoke Helm.

        Args:
            commands: A CommandRunner instance.
            catalog: A ChartCatalog instance.
            helm: A HelmClient instance.
        """
        self.commands = commands
        self.catalog = catalog
        self.helm = helm

    def lint_all(self):
        """Lint every chart except the skipped ones, after registering the Helm repositories."""
        self.helm.add_repositories()
        for metadata in sorted((self.catalog.root / 'charts').glob('*/Chart.yaml')):
            chart = metadata.parent
            if chart.name in SKIPPED_LINT_CHARTS:
                continue
            LOGGER.info('Linting %s', chart.name)
            self.helm.dependencies(chart)
            self.helm.lint(chart)

    def validate(self, chart):
        """Lint with each example, run unit tests, and check that rendered examples pass kubeconform."""
        chart = Path(chart).resolve()
        metadata = self.catalog.metadata(chart)
        self.helm.dependencies(chart)
        for example in ('minimal', 'full'):
            self.helm.lint(chart, values=chart / 'examples' / f'{example}.yaml')

        tests = chart / 'tests'
        if tests.is_dir() and any(tests.rglob('*_test.yaml')):
            self.commands.run(['helm', 'unittest', chart])
        if tests.is_dir() and any(tests.rglob('test_*.py')):
            self.commands.run([sys.executable, '-m', 'unittest', 'discover', '-s', tests, '-p', 'test_*.py', '-v'])

        if metadata.get('type') == 'library':
            LOGGER.info('%s is a library chart: render test skipped', chart.name)
            return

        output_dir = self.catalog.root / 'dist' / 'render'
        output_dir.mkdir(parents=True, exist_ok=True)
        for example in ('minimal', 'full'):
            rendered = self.helm.render(chart, chart / 'examples' / f'{example}.yaml')
            resources = [resource for resource in yaml.safe_load_all(rendered) if resource]
            if not resources or not all(isinstance(resource, dict) and resource.get('kind') for resource in resources):
                raise ValueError(f'{chart.name}: {example} renders no valid resources')
            output = output_dir / f'{chart.name}-{example}.yaml'
            output.write_text(rendered, encoding='utf-8')
            self.commands.run([
                'kubeconform', '-summary', '-schema-location', 'default',
                '-schema-location', CRD_SCHEMA_LOCATION, '-skip', 'CustomResourceDefinition', output,
            ])
