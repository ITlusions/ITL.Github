"""Scan one rendered chart manifest with Kubescape and fail on findings at or above the blocking severity."""

from helm_pipeline.security.reports import ScanReport

# AI generated code: GitHub Copilot Claude Haiku 5.5
BLOCKING_SEVERITY = 'critical'
REPORT_FILE = 'kubescape.json'


class KubescapeScanner:
    """Run Kubescape misconfiguration controls against rendered manifests."""

    def __init__(self, commands):
        """Store the command runner used to invoke Kubescape.

        Args:
            commands: A CommandRunner instance.
        """
        self.commands = commands

    def scan(self, scan_report, manifest, output, exceptions=None):
        """Fail when Kubescape reports failed controls at or above the blocking severity.

        Kubescape exits with code 1 when a failed control reaches the threshold. The full JSON report is
        written next to the Trivy reports so it can be uploaded as an artifact. An exception file suppresses
        the listed controls for the listed resources, so their findings no longer block the scan.

        Args:
            scan_report: ScanReport that records a failure.
            manifest: Path to the rendered manifest.
            output: Report directory of the chart.
            exceptions: Optional path to a Kubescape exception file of the chart.
        """
        arguments = ['kubescape', 'scan', manifest, '--format', 'json', '--output', output / REPORT_FILE,
                     '--severity-threshold', BLOCKING_SEVERITY, '--keep-local']
        if exceptions:
            arguments += ['--exceptions', exceptions]
        scan_report.run(self.commands, 'kubescape', arguments)
