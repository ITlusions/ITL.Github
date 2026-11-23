"""Run the Trivy config and image scans and summarize the high-severity findings."""

import hashlib
import json
import logging
import subprocess

LOGGER = logging.getLogger(__name__)
# AI generated code: GitHub Copilot Claude Haiku 5.5
BLOCKING_SEVERITY = 'HIGH,CRITICAL'
VULNERABILITY_REPORT = 'vulnerabilities.json'
VULNERABILITY_HEADERS = ['Severity', 'Image', 'CVE', 'Package', 'Installed', 'Fixed', 'Title']
SEVERITY_ORDER = {'CRITICAL': 0, 'HIGH': 1}


class TrivyScanner:
    """Run Trivy configuration and image scans against rendered manifests and images."""

    def __init__(self, commands, github):
        """Store the command runner and the GitHub file writer.

        Args:
            commands: A CommandRunner instance.
            github: A GitHubFiles instance.
        """
        self.commands = commands
        self.github = github

    def identifier(self, image):
        """Return a short, stable identifier for an image reference, used in report file names."""
        return hashlib.sha256(image.encode('utf-8')).hexdigest()[:16]

    def config_scan(self, scan_report, manifest, output, exceptions):
        """Fail on HIGH and CRITICAL misconfigurations that the exception file does not suppress.

        Args:
            scan_report: ScanReport that records a failure.
            manifest: Path to the rendered manifest.
            output: Report directory of the chart.
            exceptions: Path to the exception file, or None.
        """
        arguments = ['trivy', 'config', '--severity', BLOCKING_SEVERITY, '--format', 'json', '--exit-code', '1',
                     '--output', output / 'config.json']
        if exceptions:
            arguments += ['--ignorefile', exceptions]
        scan_report.run(self.commands, 'trivy config', arguments + [manifest])

    def unfiltered_config(self, report_file, manifest):
        """Write a Trivy config report without exclusions so suppressed findings can be listed."""
        self.commands.run(['trivy', 'config', '--severity', BLOCKING_SEVERITY, '--format', 'json', '--output',
                           report_file, manifest])

    def image_scan(self, scan_report, image, output):
        """Fail on CRITICAL vulnerabilities with a fix available in one container image."""
        report_file = output / f'image-{self.identifier(image)}.json'
        arguments = ['trivy', 'image', '--scanners', 'vuln', '--severity', 'CRITICAL', '--ignore-unfixed',
                     '--format', 'json', '--exit-code', '1', '--output', report_file, image]
        scan_report.run(self.commands, f'trivy image {image}', arguments)

    def high_report(self, name, output, images):
        """Count HIGH vulnerabilities per image and add a job summary table without failing the scan."""
        rows = []
        for image in sorted(images):
            report_file = output / f'image-high-{self.identifier(image)}.json'
            try:
                self.commands.run(['trivy', 'image', '--scanners', 'vuln', '--severity', 'HIGH', '--ignore-unfixed',
                                   '--format', 'json', '--output', report_file, image])
            except subprocess.CalledProcessError:
                LOGGER.warning('%s: HIGH vulnerability report failed for %s', name, image)
                rows.append((image, 'scan failed'))
                continue
            count = self.count_vulnerabilities(report_file)
            LOGGER.warning('%s: %d HIGH vulnerabilit%s in %s', name, count, 'y' if count == 1 else 'ies', image)
            rows.append((image, str(count)))
        if rows:
            self.github.append_table(f'HIGH image vulnerabilities: {name}', ['Image', 'HIGH findings'], rows)
        self.vulnerability_report(name, output, images)

    def vulnerability_report(self, name, output, images):
        """Write every CRITICAL and HIGH CVE to a JSON report and add a job summary table."""
        findings = []
        for image in sorted(images):
            identifier = self.identifier(image)
            findings += self.read_vulnerabilities(output / f'image-{identifier}.json', image)
            findings += self.read_vulnerabilities(output / f'image-high-{identifier}.json', image)
        findings.sort(key=self.sort_key)
        (output / VULNERABILITY_REPORT).write_text(json.dumps(findings, indent=2) + '\n', encoding='utf-8')
        if findings:
            rows = [(item['severity'], item['image'], item['id'], item['package'], item['installed'], item['fixed'],
                     item['title']) for item in findings]
            self.github.append_table(f'Image vulnerabilities: {name}', VULNERABILITY_HEADERS, rows)

    def sort_key(self, finding):
        """Order CRITICAL before HIGH, then by image and CVE identifier."""
        return (SEVERITY_ORDER.get(finding['severity'], len(SEVERITY_ORDER)), finding['image'], finding['id'])

    def read_vulnerabilities(self, report_file, image):
        """Return one dict per vulnerability in a Trivy image JSON report, or an empty list when it is missing."""
        if not report_file.is_file():
            return []
        findings = []
        for result in json.loads(report_file.read_text(encoding='utf-8')).get('Results') or []:
            for item in result.get('Vulnerabilities') or []:
                findings.append({
                    'image': image,
                    'severity': item.get('Severity', ''),
                    'id': item.get('VulnerabilityID', ''),
                    'package': item.get('PkgName', ''),
                    'installed': item.get('InstalledVersion', ''),
                    'fixed': item.get('FixedVersion', ''),
                    'title': item.get('Title', ''),
                })
        return findings

    def count_vulnerabilities(self, report_file):
        """Return the number of vulnerabilities listed in a Trivy image JSON report."""
        if not report_file.is_file():
            return 0
        data = json.loads(report_file.read_text(encoding='utf-8'))
        count = 0
        for result in data.get('Results') or []:
            count += len(result.get('Vulnerabilities') or [])
        return count
