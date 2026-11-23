"""Compose the chart CI services for one repository root and expose them as CI steps."""

import subprocess
from pathlib import Path

from helm_pipeline.charts.catalog import ChartCatalog
from helm_pipeline.charts.changes import ChangeDetector
from helm_pipeline.charts.config import ChartConfig
from helm_pipeline.charts.helm import HelmClient
from helm_pipeline.charts.kind import KindTester
from helm_pipeline.charts.lockfiles import LockChecker
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
        self.locks = LockChecker(self.catalog)
        self.versioner = ReleaseVersioner(self.commands, self.catalog, self.github)
        self.changes = ChangeDetector(self.commands, self.catalog, self.github, self.versioner)
        self.validator = ChartValidator(self.commands, self.catalog, self.helm)
        self.publisher = ChartPublisher(self.catalog, self.helm)
        self.packager = ChartPackager(self.catalog, self.helm)
        self.renderer = RenderDiffer(self.commands, self.catalog, self.helm, self.github)
        self.tools = ChartToolInstaller(ToolInstaller(VerifiedDownloader()), self.helm, self.github, self.pins)
        self.kind = KindTester(self.commands)

    def run(self, args, **kwargs):
        """Run an external command from the repository root and return its completed process."""
        return self.commands.run(args, **kwargs)

    def chart_config(self, chart):
        """Return the validated settings of a chart's .ciconfig file."""
        return self.config.read(chart)

    def write_chart_config(self, chart):
        """Write a chart's .ciconfig settings as GitHub Actions outputs."""
        self.config.write_outputs(chart)

    def kind_plan(self, chart, scenario, kube_version, cluster_name):
        """Return the kind commands for one scenario of a chart without running them."""
        return self.kind.plan_for(chart, self.config.kind_settings(chart), scenario, kube_version, cluster_name)

    def kind_test(self, chart, scenario, kube_version, cluster_name, keep_cluster=False):
        """Install and test one kind scenario of a chart in a kind cluster."""
        self.kind.run(chart, self.config.kind_settings(chart), scenario, kube_version, cluster_name, keep_cluster)

    def add_repositories(self):
        """Register the Helm chart repositories that charts depend on."""
        self.helm.add_repositories()

    def write_security_charts(self, affected):
        """Write the affected charts that run at least one security scanner."""
        self.config.write_security_charts(affected)

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

    def check_locks(self, chart=None):
        """Raise when a chart's Chart.lock, or any non-ignored chart's, pins a stale local dependency version."""
        self.locks.check(chart)

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
