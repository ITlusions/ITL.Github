"""Find exclusions that have expired, expire soon, or no longer match anything that the scanners report."""

from dataclasses import dataclass
from datetime import date

from helm_pipeline.security.chart_exceptions import STATUS_EXPIRED
from helm_pipeline.security.kubescape_report import KubescapeReport


EXPIRING_WITHIN_DAYS = 30
KIND_EXPIRED = 'expired'
KIND_EXPIRING = 'expiring'
KIND_STALE = 'stale'
KUBESCAPE_CONTROL_SEPARATOR = ', '


@dataclass(frozen=True)
class ExclusionIssue:
    """One exclusion of a chart that needs attention, with the reason it was flagged."""

    kind: str
    scanner: str
    identifier: str
    message: str


class ExclusionAudit:
    """Classify the exclusions of one chart against the reference date and the scanner reports."""

    def __init__(self, today, misconfigurations):
        """Store the reference date and the reader for Trivy misconfiguration reports.

        Args:
            today: Date that expiry is judged against.
            misconfigurations: A MisconfigurationReport instance used to read the unfiltered Trivy report.
        """
        self.today = today
        self.misconfigurations = misconfigurations

    def audit(self, rows, trivy_report, kubescape_report):
        """Return the exclusions that have expired, expire soon, or are stale.

        An exclusion is stale when its scanner report exists but does not contain the finding the exclusion names.
        Without a scanner report there is nothing to compare against, so no stale issue is raised for that scanner.

        Args:
            rows: Exclusion rows as returned by ChartExceptions.exclusions().
            trivy_report: Path to the unfiltered Trivy misconfiguration report.
            kubescape_report: Path to the Kubescape JSON report.

        Returns:
            A list of ExclusionIssue in the order of the rows.
        """
        trivy_ids = self.trivy_ids(trivy_report)
        kubescape_ids = self.kubescape_ids(kubescape_report)
        issues = []
        for row in rows:
            issue = self.classify(row, trivy_ids, kubescape_ids)
            if issue is not None:
                issues.append(issue)
        return issues

    def classify(self, row, trivy_ids, kubescape_ids):
        """Return the issue of one exclusion, or None when it is active, not expiring soon, and still reported.

        Args:
            row: One exclusion row as returned by ChartExceptions.exclusions().
            trivy_ids: Misconfiguration IDs in the Trivy report, or None when the report does not exist.
            kubescape_ids: Control IDs in the Kubescape report, or None when the report does not exist.

        Returns:
            An ExclusionIssue, or None.
        """
        if row['status'] == STATUS_EXPIRED:
            return ExclusionIssue(KIND_EXPIRED, row['scanner'], row['id'],
                                  f'expired on {row["expires"]} and no longer applies')
        if self.is_stale(row, trivy_ids, kubescape_ids):
            return ExclusionIssue(KIND_STALE, row['scanner'], row['id'],
                                  'no longer matches a finding that the scanner reports')
        days = (date.fromisoformat(row['expires']) - self.today).days
        if days <= EXPIRING_WITHIN_DAYS:
            return ExclusionIssue(KIND_EXPIRING, row['scanner'], row['id'],
                                  f'expires in {days} day(s) on {row["expires"]}')
        return None

    def is_stale(self, row, trivy_ids, kubescape_ids):
        """Return True when the scanner report exists and does not contain the finding that the exclusion names."""
        if row['scanner'] == 'trivy':
            return trivy_ids is not None and row['id'] not in trivy_ids
        controls = row['id'].split(KUBESCAPE_CONTROL_SEPARATOR)
        return kubescape_ids is not None and not any(control in kubescape_ids for control in controls)

    def trivy_ids(self, report):
        """Return the misconfiguration IDs in the unfiltered Trivy report, or None when the report does not exist."""
        if not report.is_file():
            return None
        return {entry[1] for entry in self.misconfigurations.read(report)}

    def kubescape_ids(self, report):
        """Return the control IDs in the Kubescape report, or None when the report does not exist."""
        if not report.is_file():
            return None
        return KubescapeReport(report).control_ids()
