"""Scan the repository git history for secrets and audit the installed Python packages."""

import json
import logging
import subprocess
import sys
from pathlib import Path

from helm_pipeline.security.reports import ScanReport

LOGGER = logging.getLogger(__name__)



class RepositoryScanner:
    """Run gitleaks over the git history and pip-audit over the installed Python packages."""

    def __init__(self, root, commands):
        """Store the repository root and the command runner.

        Args:
            root: Repository root directory.
            commands: A CommandRunner instance rooted at the repository.
        """
        self.root = Path(root)
        self.commands = commands

    def new_report(self):
        """Create the repository report directory, clear old errors, and return its ScanReport."""
        report = ScanReport(self.root / 'dist' / 'security' / 'repository')
        report.directory.mkdir(parents=True, exist_ok=True)
        report.clear()
        return report

    def scan_secrets(self, base=None):
        """Run gitleaks over the git history, optionally limited to commits after a base revision.

        Args:
            base: Revision after which commits are scanned, or None for the full history.
        """
        report = self.new_report()
        LOGGER.info('Scanning git history for secrets (base: %s)', base or 'all commits')
        command = ['gitleaks', 'git', '--redact=100', '--exit-code', '1', '--report-format', 'json',
                   '--report-path', report.directory / 'gitleaks.json']
        if base:
            command.append(f'--log-opts={base}..HEAD')
        report.run(self.commands, 'gitleaks', command + [self.root])

    def audit_dependencies(self):
        """Run pip-audit over the installed Python packages and write its JSON report."""
        report = self.new_report()
        output = report.directory / 'pip-audit.json'
        LOGGER.info('Auditing installed Python packages, report: %s', output)
        result = self.commands.run([sys.executable, '-m', 'pip_audit', '--format', 'json', '--output', output],
                                   check=False)
        if result.returncode:
            self.check_audit_failure(report, output, result)

    def check_audit_failure(self, report, output, result):
        """Treat pip-audit exit code 1 as a finding report, and any other failure as a scan error.

        Vulnerabilities listed in the report are informational and do not fail the scan.

        Args:
            report: ScanReport that records failures.
            output: Path to the pip-audit JSON report.
            result: The completed process of the failed pip-audit run.

        Raises:
            subprocess.CalledProcessError: When pip-audit failed for a reason other than reported vulnerabilities.
            RuntimeError: When the pip-audit report is not valid JSON or lists no vulnerabilities.
        """
        if result.returncode != 1 or not output.is_file():
            report.record_error('pip-audit', f'exit code {result.returncode}')
            raise subprocess.CalledProcessError(result.returncode, result.args)
        try:
            data = json.loads(output.read_text(encoding='utf-8'))
        except (OSError, ValueError) as error:
            report.record_error('pip-audit', 'report is not valid JSON')
            raise RuntimeError('pip-audit could not write a valid report') from error
        if not self.lists_vulnerabilities(data):
            report.record_error('pip-audit', 'failed without reported vulnerabilities')
            raise RuntimeError('pip-audit failed without reported vulnerabilities')

    def lists_vulnerabilities(self, data):
        """Return True when a parsed pip-audit report lists at least one vulnerability."""
        if not isinstance(data, dict):
            return False
        for dependency in data.get('dependencies') or []:
            if isinstance(dependency, dict) and dependency.get('vulns'):
                return True
        return False

    def scan_repository(self):
        """Run the secret scan over the full history and the dependency audit."""
        self.scan_secrets()
        self.audit_dependencies()
