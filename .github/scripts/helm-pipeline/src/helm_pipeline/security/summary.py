"""Write the job summary of a security step from the report files that the step left behind."""

import json
from pathlib import Path

from helm_pipeline.security.chart_exceptions import ChartExceptions
from helm_pipeline.security.exclusion_audit import ExclusionAudit
from helm_pipeline.security.kubescape_report import KubescapeReport
from helm_pipeline.security.misconfigurations import MisconfigurationReport
from helm_pipeline.security.reports import ERROR_REPORT
from helm_pipeline.security.summary_layouts import (
    DEFAULT_LAYOUT,
    STATUS_BLOCKING,
    ChartFindings,
    SummaryLayoutFactory,
)

# AI generated code: GitHub Copilot Claude Haiku 5.5
GITLEAKS_REPORT = 'gitleaks.json'
PIP_AUDIT_REPORT = 'pip-audit.json'
IMAGES_REPORT = 'images.json'
TRIVY_CONFIG_REPORT = 'config.json'
TRIVY_UNFILTERED_REPORT = 'config-unfiltered.json'
KUBESCAPE_REPORT = 'kubescape.json'
REPOSITORY_DIRECTORY = 'repository'
RESULT_HEADERS = ['Scanner', 'Result', 'Detail']
ERROR_HEADERS = ['Scanner', 'Message']
SECRET_HEADERS = ['File', 'Line', 'Rule', 'Description']
DEPENDENCY_HEADERS = ['Package', 'Version', 'Vulnerability', 'Fix versions']


class SecuritySummary:
    """Add the outcome of one security step to the GitHub job summary."""

    def __init__(self, github, root, layout=DEFAULT_LAYOUT, verifier=None):
        """Store the GitHub file writer, the repository root, the chart summary layout and the signature verifier.

        Args:
            github: A GitHubFiles instance.
            root: Repository root directory.
            layout: Name of the chart summary layout: classic, flat, sections, counts or expiry.
            verifier: An ExceptionSignatureVerifier used when reading exceptions, or None to skip verification.

        Raises:
            ValueError: When the layout name is unknown.
        """
        self.github = github
        self.root = Path(root)
        self.layout = SummaryLayoutFactory().create(layout)
        self.verifier = verifier

    def write(self, command, chart=None):
        """Write the summary for a finished security step; steps without a summary are ignored.

        Args:
            command: Name of the security-scan subcommand that ran.
            chart: Chart name or path, used by the chart command only.
        """
        if command == 'chart':
            self.chart(chart)
        elif command == 'secrets':
            self.secrets()
        elif command == 'dependencies':
            self.dependencies()

    def chart(self, chart):
        """Add the scanner results of one chart, and any scanner errors, to the job summary."""
        name = Path(chart).name
        output = self.root / 'dist' / 'security' / name
        errors = self.errors(output)
        exceptions = ChartExceptions(self.root, self.github, verifier=self.verifier)
        exclusions = exceptions.exclusions(name)
        findings = ChartFindings(KubescapeReport(output / KUBESCAPE_REPORT).failing_controls(), exclusions)
        blocking = findings.with_status(STATUS_BLOCKING)
        rows = [
            ('Trivy misconfigurations', self.result(output / TRIVY_CONFIG_REPORT, errors, 'trivy config'), '-'),
            ('Kubescape', self.result(output / KUBESCAPE_REPORT, errors, 'kubescape', bool(blocking)), '-'),
            ('Trivy image scans', self.result(output / IMAGES_REPORT, errors, 'trivy image'),
             f'{len(self.load_json(output / IMAGES_REPORT, []))} image(s)'),
        ]
        self.github.append_table(f'Chart security: {name}', RESULT_HEADERS, rows)
        for finding in blocking:
            self.github.annotate('warning', f'Kubescape {finding.identifier}',
                                 f'{finding.name}: failed on {finding.resources} resource(s) in {name}')
        audit = ExclusionAudit(exceptions.today, MisconfigurationReport(self.github))
        for issue in audit.audit(exclusions, output / TRIVY_UNFILTERED_REPORT, output / KUBESCAPE_REPORT):
            self.github.annotate('warning', f'Exclusion {issue.kind}: {issue.identifier}',
                                 f'{issue.scanner} {issue.identifier} in {name}: {issue.message}')
        self.layout.render(self.github, name, findings)
        self.write_errors(errors)

    def secrets(self):
        """Add the gitleaks result and its findings to the job summary; secret values are never printed."""
        output = self.root / 'dist' / 'security' / REPOSITORY_DIRECTORY
        errors = self.errors(output)
        findings = self.load_json(output / GITLEAKS_REPORT, [])
        if findings:
            errors = [error for error in errors if not error['scanner'].startswith('gitleaks')]
        result = self.result(output / GITLEAKS_REPORT, errors, 'gitleaks', bool(findings))
        detail = f'{len(findings)} finding(s)'
        self.github.append_table('Secret scan', RESULT_HEADERS, [('gitleaks', result, detail)])
        rows = [(item.get('File', ''), item.get('StartLine', ''), item.get('RuleID', ''), item.get('Description', ''))
                for item in findings]
        if rows:
            self.github.append_table('Secret findings', SECRET_HEADERS, rows)
        self.write_errors(errors)

    def dependencies(self):
        """Add the pip-audit result and every reported vulnerability to the job summary."""
        output = self.root / 'dist' / 'security' / REPOSITORY_DIRECTORY
        errors = self.errors(output)
        report = self.load_json(output / PIP_AUDIT_REPORT, {})
        rows = []
        for package in report.get('dependencies') or []:
            for vulnerability in package.get('vulns') or []:
                rows.append((package.get('name', ''), package.get('version', ''), vulnerability.get('id', ''),
                             ', '.join(vulnerability.get('fix_versions') or []) or '-'))
        result = self.result(output / PIP_AUDIT_REPORT, errors, 'pip-audit', bool(rows))
        self.github.append_table('Dependency audit', RESULT_HEADERS,
                                 [('pip-audit', result, f'{len(rows)} vulnerability(ies)')])
        if rows:
            self.github.append_table('Vulnerable dependencies', DEPENDENCY_HEADERS, rows)
        self.write_errors(errors)

    def result(self, report, errors, prefix, found=False):
        """Return failed, findings, passed or skipped for one scanner.

        Args:
            report: Report file the scanner writes when it runs.
            errors: Scanner errors recorded in the report directory.
            prefix: Scanner name prefix that marks a scanner error.
            found: True when the scanner reported findings.

        Returns:
            One of 'failed', 'findings', 'passed' or 'skipped'.
        """
        if any(error['scanner'].startswith(prefix) for error in errors) and not found:
            return 'failed'
        if not report.is_file():
            return 'skipped'
        return 'findings' if found else 'passed'

    def errors(self, directory):
        """Return the scanner errors recorded in a report directory."""
        return self.load_json(directory / ERROR_REPORT, [])

    def write_errors(self, errors):
        """Add a table of scanner errors to the job summary when there are any."""
        if errors:
            self.github.append_table('Scanner errors', ERROR_HEADERS,
                                     [(error['scanner'], error['message']) for error in errors])

    def load_json(self, path, default):
        """Return the parsed JSON file, or the default when the file is missing or empty."""
        if not path.is_file():
            return default
        data = json.loads(path.read_text(encoding='utf-8'))
        return data or default
