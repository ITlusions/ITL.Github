"""Compose the security scanners for one repository root and expose them as CI steps."""

import subprocess
from pathlib import Path

from helm_pipeline.charts.catalog import ChartCatalog
from helm_pipeline.charts.config import ChartConfig
from helm_pipeline.charts.helm import HelmClient
from helm_pipeline.core.commands import CommandRunner
from helm_pipeline.core.downloads import VerifiedDownloader
from helm_pipeline.core.github import GitHubFiles
from helm_pipeline.core.settings import ToolPins
from helm_pipeline.core.tools import ToolInstaller
from helm_pipeline.security.chart_exceptions import ChartExceptions
from helm_pipeline.security.chart_scan import ChartScanner
from helm_pipeline.security.exception_signature import ExceptionSignatureVerifier
from helm_pipeline.security.images import ImageFinder
from helm_pipeline.security.kubescape import KubescapeScanner
from helm_pipeline.security.misconfigurations import MisconfigurationReport
from helm_pipeline.security.renderer import ChartRenderer
from helm_pipeline.security.repository import RepositoryScanner
from helm_pipeline.security.tools import SecurityToolInstaller
from helm_pipeline.security.trivy import TrivyScanner

# AI generated code: GitHub Copilot Claude Haiku 5.5


class SecurityPipeline:
    """Compose the security scanners for one repository root and expose them as CI steps."""

    def __init__(self, root, runner=subprocess.run, pins=None, verify_exceptions=False):
        """Wire the scanners together for the repository root.

        Args:
            root: Repository root directory.
            runner: Callable that runs processes, injected for tests that need a different runner.
            pins: A ToolPins instance; loads the packaged config.yaml when omitted.
            verify_exceptions: When True, every exception file must carry a valid cosign signature.
        """
        self.root = Path(root).resolve()
        self.commands = CommandRunner(self.root, runner)
        self.pins = pins if pins is not None else ToolPins.load()
        self.github = GitHubFiles()
        self.helm = HelmClient(self.commands, ChartCatalog(self.root))
        self.tools = SecurityToolInstaller(ToolInstaller(VerifiedDownloader()), self.github, self.pins)
        self.repository = RepositoryScanner(self.root, self.commands)
        self.charts = ChartScanner(
            self.root,
            ChartConfig(self.root, self.github),
            ChartRenderer(self.commands, self.helm),
            TrivyScanner(self.commands, self.github),
            KubescapeScanner(self.commands),
            ChartExceptions(self.root, self.github, verifier=self.exception_verifier(verify_exceptions)),
            MisconfigurationReport(self.github),
            ImageFinder(),
        )

    @staticmethod
    def exception_verifier(enabled):
        """Return a signature verifier when verification is enabled, otherwise None."""
        return ExceptionSignatureVerifier() if enabled else None

    def setup_tools(self, directory, tools):
        """Install the named security tools into a directory and add it to PATH."""
        self.tools.setup_tools(directory, tools)

    def scan_chart(self, chart):
        """Scan one chart's rendered manifests and images."""
        self.charts.scan(chart)

    def scan_secrets(self, base=None):
        """Scan the git history for secrets, optionally after a base revision."""
        self.repository.scan_secrets(base)

    def audit_dependencies(self):
        """Audit the installed Python packages."""
        self.repository.audit_dependencies()

    def scan_repository(self):
        """Run the full repository scan: secrets and dependencies."""
        self.repository.scan_repository()
