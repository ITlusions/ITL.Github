"""Scan one rendered chart manifest with Kubescape and report findings at or above the blocking severity as warnings."""

import logging
import subprocess

from helm_pipeline.security.reports import ScanReport

LOGGER = logging.getLogger(__name__)
# AI generated code: GitHub Copilot Claude Haiku 5.5
BLOCKING_SEVERITY = 'critical'
REPORT_FILE = 'kubescape.json'
# Kubescape exits with this code when failed controls reach the severity threshold.
FINDINGS_EXIT_CODE = 1


class KubescapeScanner:
    """Run Kubescape misconfiguration controls against rendered manifests."""

    def __init__(self, commands):
        """Store the command runner used to invoke Kubescape.

        Args:
            commands: A CommandRunner instance.
        """
        self.commands = commands

    def scan(self, scan_report, manifest, output, exceptions=None):
        """Run Kubescape and treat failed controls at or above the blocking severity as warnings.

        Kubescape exits with code 1 when a failed control reaches the threshold. That outcome does not fail the
        scan: the findings are read from the JSON report and shown as warning annotations and in the job summary.
        Any other non-zero exit code is a scanner error and is recorded and raised. The full JSON report is
        written next to the Trivy reports so it can be uploaded as an artifact. An exception file suppresses
        the listed controls for the listed resources, so their findings are no longer reported.

        Args:
            scan_report: ScanReport that records a scanner error.
            manifest: Path to the rendered manifest.
            output: Report directory of the chart.
            exceptions: Optional path to a Kubescape exception file of the chart.

        Raises:
            subprocess.CalledProcessError: When Kubescape fails for a reason other than findings.
        """
        arguments = ['kubescape', 'scan', manifest, '--format', 'json', '--output', output / REPORT_FILE,
                     '--severity-threshold', BLOCKING_SEVERITY, '--keep-local']
        if exceptions:
            arguments += ['--exceptions', exceptions]
        try:
            self.commands.run(arguments)
        except subprocess.CalledProcessError as error:
            if error.returncode != FINDINGS_EXIT_CODE:
                scan_report.record_error('kubescape', f'exited with code {error.returncode}; see the findings above')
                raise
            LOGGER.warning('kubescape: failed controls at or above %s are reported as warnings', BLOCKING_SEVERITY)
