"""Render the findings and exclusions of one chart in a selectable job summary layout."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date

# AI generated code: GitHub Copilot Claude Haiku 5.5
DEFAULT_LAYOUT = 'classic'
NOT_APPLICABLE = '-'
STATUS_BLOCKING = 'blocking'
STATUS_EXCLUDED = 'excluded'
STATUS_EXPIRED = 'expired'
STATUS_ORDER = (STATUS_BLOCKING, STATUS_EXCLUDED, STATUS_EXPIRED)
EXCLUSION_STATUS_ACTIVE = 'active'
CONTROL_HEADERS = ['Control', 'Name', 'Failed resources']
FINDING_HEADERS = ['Scanner', 'ID', 'Name', 'Failed resources', 'Status', 'Owner', 'Expires', 'Request']
COUNT_HEADERS = ['Status', 'Count']
EXPIRY_HEADERS = ['Expires', 'Days left', 'Scanner', 'ID', 'Owner', 'Request', 'Status']


@dataclass(frozen=True)
class Finding:
    """One finding of a chart: a failing control or an exclusion, with its status and metadata."""

    scanner: str
    identifier: str
    name: str
    resources: str
    status: str
    owner: str
    expires: str
    request: str

    def row(self):
        """Return the finding as a table row in the order of FINDING_HEADERS."""
        return (self.scanner, self.identifier, self.name, self.resources, self.status, self.owner, self.expires,
                self.request)


class ChartFindings:
    """Combine the failing Kubescape controls and the exclusions of one chart into findings."""

    def __init__(self, failing, exclusions):
        """Store the failing controls and the exclusion rows of one chart.

        Args:
            failing: Failing controls as returned by KubescapeReport.failing_controls().
            exclusions: Exclusion rows as returned by ChartExceptions.exclusions().
        """
        self.failing = failing
        self.exclusions = exclusions

    def all(self):
        """Return every finding, ordered blocking, excluded and expired."""
        findings = []
        for status in STATUS_ORDER:
            findings.extend(self.with_status(status))
        return findings

    def with_status(self, status):
        """Return the findings with one status, in the order they were reported."""
        if status == STATUS_BLOCKING:
            return [self.blocking(item) for item in self.failing]
        return [self.exclusion(row) for row in self.exclusions if self.exclusion_status(row) == status]

    def blocking(self, item):
        """Return a failing control as a blocking finding."""
        return Finding('kubescape', item['id'], item['name'], str(item['resources']), STATUS_BLOCKING,
                       NOT_APPLICABLE, NOT_APPLICABLE, NOT_APPLICABLE)

    def exclusion(self, row):
        """Return an exclusion row as an excluded or expired finding."""
        return Finding(row['scanner'], row['id'], row['detail'], NOT_APPLICABLE, self.exclusion_status(row),
                       row['owner'], row['expires'], row['request'])

    def exclusion_status(self, row):
        """Return excluded for an active exclusion and expired for one that has passed its expiry date."""
        if row['status'] == EXCLUSION_STATUS_ACTIVE:
            return STATUS_EXCLUDED
        return STATUS_EXPIRED


class SummaryLayout(ABC):
    """Write the findings of one chart to the job summary in one layout."""

    @abstractmethod
    def render(self, github, chart, findings):
        """Add the findings of one chart to the job summary.

        Args:
            github: A GitHubFiles instance.
            chart: Chart name used in table titles.
            findings: A ChartFindings instance.
        """


class ClassicLayout(SummaryLayout):
    """Show the failing Kubescape controls in one table, as the summary has always done."""

    def render(self, github, chart, findings):
        """Add the table of failing controls when there are any."""
        controls = findings.with_status(STATUS_BLOCKING)
        if controls:
            github.append_table('Kubescape failing controls', CONTROL_HEADERS,
                                [(item.identifier, item.name, item.resources) for item in controls])


class FlatLayout(SummaryLayout):
    """Show every finding in one table with its status, owner, expiry and request."""

    def render(self, github, chart, findings):
        """Add one table with all findings of the chart when there are any."""
        rows = [finding.row() for finding in findings.all()]
        if rows:
            github.append_table(f'Findings: {chart}', FINDING_HEADERS, rows)


class SectionLayout(SummaryLayout):
    """Show blocking findings, excluded findings and expired exclusions in separate tables."""

    TITLES = {
        STATUS_BLOCKING: 'Blocking findings',
        STATUS_EXCLUDED: 'Excluded findings',
        STATUS_EXPIRED: 'Expired exclusions',
    }

    def render(self, github, chart, findings):
        """Add one table per status that has at least one finding."""
        for status in STATUS_ORDER:
            rows = [finding.row() for finding in findings.with_status(status)]
            if rows:
                github.append_table(f'{self.TITLES[status]}: {chart}', FINDING_HEADERS, rows)


class CountLayout(SummaryLayout):
    """Show how many findings have each status, then list only the blocking findings."""

    def render(self, github, chart, findings):
        """Add a count table for all statuses and a table of blocking findings when there are any."""
        counts = [(status, len(findings.with_status(status))) for status in STATUS_ORDER]
        github.append_table(f'Findings overview: {chart}', COUNT_HEADERS, counts)
        blocking = [finding.row() for finding in findings.with_status(STATUS_BLOCKING)]
        if blocking:
            github.append_table(f'Blocking findings: {chart}', FINDING_HEADERS, blocking)


class ExpiryLayout(SummaryLayout):
    """Show the blocking findings first, then the exclusions sorted by the date they expire."""

    def __init__(self, today=None):
        """Store the date that days left are counted from.

        Args:
            today: Reference date; defaults to the current date.
        """
        self.today = today or date.today()

    def render(self, github, chart, findings):
        """Add the blocking findings table and an exclusions table sorted by expiry date."""
        blocking = [finding.row() for finding in findings.with_status(STATUS_BLOCKING)]
        if blocking:
            github.append_table(f'Blocking findings: {chart}', FINDING_HEADERS, blocking)
        exclusions = findings.with_status(STATUS_EXCLUDED) + findings.with_status(STATUS_EXPIRED)
        exclusions.sort(key=self.expiry_date)
        if exclusions:
            rows = [self.expiry_row(finding) for finding in exclusions]
            github.append_table(f'Exclusions by expiry: {chart}', EXPIRY_HEADERS, rows)

    def expiry_date(self, finding):
        """Return the expiry date of a finding, or the latest possible date when it has none."""
        if finding.expires == NOT_APPLICABLE:
            return date.max
        return date.fromisoformat(finding.expires)

    def expiry_row(self, finding):
        """Return an exclusion as a row with the number of days left until it expires."""
        days = (self.expiry_date(finding) - self.today).days
        return (finding.expires, days, finding.scanner, finding.identifier, finding.owner, finding.request,
                finding.status)


class SummaryLayoutFactory:
    """Create the summary layout that is named in the configuration."""

    LAYOUTS = {
        'classic': ClassicLayout,
        'flat': FlatLayout,
        'sections': SectionLayout,
        'counts': CountLayout,
        'expiry': ExpiryLayout,
    }

    def create(self, name):
        """Return a new layout instance for a layout name.

        Args:
            name: One of classic, flat, sections, counts or expiry.

        Raises:
            ValueError: When the name is not a known layout.
        """
        if name not in self.LAYOUTS:
            raise ValueError(f'unknown summary layout {name!r}; choose one of: {", ".join(self.LAYOUTS)}')
        return self.LAYOUTS[name]()
