"""Command-line entry point for the Helm chart CI, delegating each step to a focused service class."""

import argparse
import os
import subprocess
from pathlib import Path

from helm_pipeline.charts.catalog import ChartCatalog
from helm_pipeline.charts.changes import ChangeDetector
from helm_pipeline.charts.config import ChartConfig
from helm_pipeline.charts.helm import HelmClient
from helm_pipeline.charts.packaging import ChartPackager
from helm_pipeline.charts.publishing import ChartPublisher
from helm_pipeline.charts.render_diff import RenderDiffer
from helm_pipeline.charts.requirements import RequirementsChecker
from helm_pipeline.charts.tools import ChartToolInstaller
from helm_pipeline.charts.validation import ChartValidator
from helm_pipeline.charts.versioning import ReleaseVersioner
from helm_pipeline.core.commands import CommandRunner
from helm_pipeline.core.downloads import VerifiedDownloader
from helm_pipeline.core.github import GitHubFiles
from helm_pipeline.core.settings import ToolPins
from helm_pipeline.core.tools import ToolInstaller
from helm_pipeline.logging_config import configure_logging


class ChartPipeline:
    """Compose the chart CI services for one repository root and expose them as CI steps."""

    def __init__(self, root, runner=subprocess.run, pins=None):
        """Wire the services together for the repository root.

        Args:
            root: Repository root that contains the charts directory.
            runner: Callable with the same signature as subprocess.run, used for every external command.
            pins: Optional ToolPins instance. When omitted, the pins come from the packaged config.yaml.
        """
        self.root = Path(root).resolve()
        self.commands = CommandRunner(self.root, runner)
        self.pins = pins if pins is not None else ToolPins.load()
        self.github = GitHubFiles()
        self.catalog = ChartCatalog(self.root)
        self.helm = HelmClient(self.commands, self.catalog)
        self.config = ChartConfig(self.root, self.github)
        self.requirements = RequirementsChecker(self.catalog)
        self.versioner = ReleaseVersioner(self.commands, self.catalog, self.github)
        self.changes = ChangeDetector(self.commands, self.catalog, self.github, self.versioner)
        self.validator = ChartValidator(self.commands, self.catalog, self.helm)
        self.publisher = ChartPublisher(self.catalog, self.helm)
        self.packager = ChartPackager(self.catalog, self.helm)
        self.renderer = RenderDiffer(self.commands, self.catalog, self.helm, self.github)
        self.tools = ChartToolInstaller(ToolInstaller(VerifiedDownloader()), self.helm, self.github, self.pins)

    def run(self, args, **kwargs):
        """Run an external command from the repository root and return its completed process."""
        return self.commands.run(args, **kwargs)

    def chart_config(self, chart):
        """Return the validated settings of a chart's .ciconfig file."""
        return self.config.read(chart)

    def write_chart_config(self, chart):
        """Write a chart's .ciconfig settings as GitHub Actions outputs."""
        self.config.write_outputs(chart)

    def add_repositories(self):
        """Register the Helm chart repositories that charts depend on."""
        self.helm.add_repositories()

    def write_changed(self, base, scan_all=False, selected_chart=None, tag=None, develop=None):
        """Write the CI matrix outputs for the changes against a base revision."""
        self.changes.write_changed(base, scan_all=scan_all, selected_chart=selected_chart, tag=tag, develop=develop)

    def setup_tools(self, directory):
        """Install the chart test tools into a directory and add it to the PATH."""
        self.tools.setup_tools(directory)

    def setup_kind(self, directory):
        """Install the kind and kubectl binaries into a directory and add it to the PATH."""
        self.tools.setup_kind(directory)

    def lint_all(self):
        """Lint every chart that is not skipped."""
        self.validator.lint_all()

    def check_requirements(self):
        """Raise when any non-ignored chart lacks a required file."""
        self.requirements.check()

    def validate(self, chart):
        """Lint, unit-test, render, and schema-check one chart."""
        self.validator.validate(chart)

    def check_version(self, chart, registry=None):
        """Check that the chart declares a version and, when a registry is given, that it is not published yet."""
        self.publisher.check_version(chart, registry=registry)

    def next_version(self, chart, ref, run_number, sha):
        """Compute and write the chart version for this build."""
        return self.versioner.next_version(chart, ref, run_number, sha)

    def render_diff(self, chart, base):
        """Write a Markdown summary of the rendered output difference against a base revision."""
        self.renderer.render_diff(chart, base)

    def package(self, chart, destination):
        """Package one chart into the destination directory and return the package path."""
        return self.packager.package(chart, destination)

    def publish(self, chart, registry, username, password):
        """Push one chart to the OCI registry after verifying its version is new."""
        self.publisher.publish(chart, registry, username, password)


def build_parser():
    """Return the argument parser with one subcommand per CI step."""
    parser = argparse.ArgumentParser(description='SpotINFO Helm chart CI')
    commands = parser.add_subparsers(dest='command', required=True)
    changed = commands.add_parser('changed')
    changed.add_argument('--base', default=os.environ.get('BASE_SHA', ''))
    changed.add_argument('--all', action='store_true', default=os.environ.get('SCAN_ALL') == '1')
    changed.add_argument('--chart', default=os.environ.get('SCAN_CHART'))
    changed.add_argument('--tag', default=os.environ.get('RELEASE_TAG') or None)
    changed.add_argument('--develop', default=None)
    commands.add_parser('chart-config').add_argument('chart', nargs='?', default=os.environ.get('CHART_PATH', '.'))
    commands.add_parser('setup-tools').add_argument('--directory', required=True)
    commands.add_parser('setup-kind').add_argument('--directory', required=True)
    commands.add_parser('lint-all')
    commands.add_parser('check-requirements')
    commands.add_parser('validate').add_argument('chart', nargs='?', default=os.environ.get('CHART'))
    commands.add_parser('check-version').add_argument('chart', nargs='?', default=os.environ.get('CHART'))
    commands.add_parser('next-version').add_argument('chart', nargs='?', default=os.environ.get('CHART'))
    diff = commands.add_parser('render-diff')
    diff.add_argument('chart', nargs='?', default=os.environ.get('CHART'))
    diff.add_argument('base', nargs='?', default=os.environ.get('BASE_SHA'))
    commands.add_parser('publish').add_argument('chart', nargs='?', default=os.environ.get('CHART'))
    package = commands.add_parser('package')
    package.add_argument('chart', nargs='?', default=os.environ.get('CHART'))
    package.add_argument('--destination', default='dist/packages')
    return parser


def main():
    """Parse the CLI arguments and run the requested CI step."""
    parser = build_parser()
    args = parser.parse_args()
    configure_logging()
    if args.command in ('validate', 'check-version', 'next-version', 'render-diff', 'publish', 'package') and not args.chart:
        parser.error('chart or CHART is required')
    if args.command == 'render-diff' and not args.base:
        parser.error('base or BASE_SHA is required')
    ci = ChartPipeline(Path.cwd())
    if args.command == 'changed':
        ci.write_changed(args.base, scan_all=args.all, selected_chart=args.chart, tag=args.tag, develop=args.develop)
    elif args.command == 'chart-config':
        ci.write_chart_config(args.chart)
    elif args.command == 'setup-tools':
        ci.setup_tools(args.directory)
    elif args.command == 'setup-kind':
        ci.setup_kind(args.directory)
    elif args.command == 'lint-all':
        ci.lint_all()
    elif args.command == 'check-requirements':
        ci.check_requirements()
    elif args.command == 'validate':
        ci.add_repositories()
        ci.validate(args.chart)
    elif args.command == 'check-version':
        ci.check_version(args.chart)
    elif args.command == 'next-version':
        ci.next_version(args.chart, os.environ.get('GITHUB_REF', ''), os.environ.get('GITHUB_RUN_NUMBER', '0'),
                        os.environ.get('GITHUB_SHA', ''))
    elif args.command == 'render-diff':
        ci.add_repositories()
        ci.render_diff(args.chart, args.base)
    elif args.command == 'package':
        ci.add_repositories()
        ci.package(args.chart, args.destination)
    elif args.command == 'publish':
        ci.publish(args.chart, os.environ.get('REGISTRY_HOST'), os.environ.get('REGISTRY_USERNAME'),
                   os.environ.get('REGISTRY_PASSWORD'))


if __name__ == '__main__':
    main()
