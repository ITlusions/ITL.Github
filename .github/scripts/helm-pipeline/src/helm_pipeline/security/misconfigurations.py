"""Read Trivy misconfiguration findings from JSON reports and show them in the log and job summary."""

import json
import logging

LOGGER = logging.getLogger(__name__)
# AI generated code: GitHub Copilot Claude Haiku 5.5
FINDING_HEADERS = ['Severity', 'ID', 'Target', 'Resource', 'Title']


class MisconfigurationReport:
    """Read Trivy misconfigurations and report them without changing the scan outcome."""

    def __init__(self, github):
        """Store the GitHub file writer used for job summaries.

        Args:
            github: A GitHubFiles instance.
        """
        self.github = github

    def read(self, report):
        """Return (severity, id, target, resource, title) tuples from a Trivy JSON report.

        Args:
            report: Path to a Trivy JSON report.

        Returns:
            The findings, or an empty list when the report is missing.
        """
        if not report.is_file():
            return []
        findings = []
        for result in json.loads(report.read_text(encoding='utf-8')).get('Results') or []:
            for item in result.get('Misconfigurations') or []:
                resource = (item.get('CauseMetadata') or {}).get('Resource') or '-'
                findings.append((item.get('Severity', ''), item.get('ID', ''), result.get('Target', ''),
                                 resource, item.get('Title', '')))
        return findings

    def log(self, name, report):
        """Log each blocking misconfiguration with a fix hint and add a job summary table."""
        if not report.is_file():
            LOGGER.error('%s: the Trivy report is missing at %s, so the scan result is unknown', name, report)
            return
        findings = self.read(report)
        for severity, identifier, target, resource, title in findings:
            LOGGER.error('%s: %s %s "%s" in %s (resource: %s)', name, severity, identifier, title, target, resource)
        if findings:
            LOGGER.error(
                '%s: %d blocking misconfiguration(s). Fix them, or accept a finding by adding its ID under '
                'trivy.misconfigurations in charts/%s/exceptions.yaml with a statement.',
                name, len(findings), name,
            )
        self.github.append_table(f'Trivy misconfigurations: {name}', FINDING_HEADERS, findings)

    def log_excluded(self, name, report, statements):
        """Warn about the findings that the exception file suppresses, without failing the scan.

        Args:
            name: Chart name used in messages.
            report: Path to an unfiltered Trivy JSON report.
            statements: Mapping of misconfiguration ID to its exclusion statement.
        """
        rows = []
        for severity, identifier, target, resource, title in self.read(report):
            if identifier in statements:
                rows.append((severity, identifier, target, resource, title, statements[identifier]))
        for severity, identifier, target, resource, title, statement in rows:
            LOGGER.warning('%s: excluded %s %s %s %s: %s (%s)', name, severity, identifier, target, resource, title,
                           statement)
        if rows:
            self.github.append_table(f'Excluded misconfigurations: {name}', FINDING_HEADERS + ['Exclusion statement'],
                                     rows)
