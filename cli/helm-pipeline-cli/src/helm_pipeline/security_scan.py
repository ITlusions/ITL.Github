import argparse
import hashlib
import io
import json
import logging
import os
import subprocess
import sys
import tarfile
import urllib.request
from pathlib import Path

import yaml

from helm_pipeline.chart_pipeline import ChartPipeline
from helm_pipeline.core.settings import ToolPins


SECURITY_TOOLS = ('gitleaks', 'trivy')
from helm_pipeline.logging_config import configure_logging

LOGGER = logging.getLogger(__name__)

# Name of the file in a report directory that lists scanners which failed to complete.
ERROR_REPORT = 'scan-errors.json'


class SecurityScanner:
    def __init__(self, root, runner=subprocess.run, pins=None):
        self.root = Path(root).resolve()
        self.runner = runner
        self.pins = pins if pins is not None else ToolPins.load()

    def run(self, args, *, check=True):
        command = [str(arg) for arg in args]
        LOGGER.info('Running %s', ' '.join(command))
        return self.runner(command, cwd=self.root, check=check, text=True, encoding='utf-8')

    def scan(self, directory, scanner, args):
        """Run a scanner and record its failure in the report directory before re-raising."""
        try:
            return self.run(args)
        except subprocess.CalledProcessError as error:
            self.record_error(directory, scanner, str(error))
            raise

    def record_error(self, directory, scanner, message):
        """Append a failed scan to the report directory so the summary can list it."""
        LOGGER.error('%s failed: %s', scanner, message)
        path = Path(directory) / ERROR_REPORT
        path.parent.mkdir(parents=True, exist_ok=True)
        errors = json.loads(path.read_text(encoding='utf-8')) if path.is_file() else []
        errors.append({'scanner': scanner, 'message': message})
        path.write_text(json.dumps(errors, indent=2) + '\n', encoding='utf-8')

    def setup_tools(self, directory, tools):
        directory = Path(directory).resolve()
        directory.mkdir(parents=True, exist_ok=True)
        for tool in tools:
            # A binary restored from the CI cache is reused without downloading it again.
            if (directory / tool).is_file():
                LOGGER.info('Reusing cached %s in %s', tool, directory)
                continue
            download = self.pins.get(tool)
            LOGGER.info('Downloading %s', download.url)
            with urllib.request.urlopen(download.url, timeout=120) as response:
                archive_data = response.read()
            if hashlib.sha256(archive_data).hexdigest() != download.sha256:
                raise ValueError(f'{tool}: checksum does not match')
            with tarfile.open(fileobj=io.BytesIO(archive_data), mode='r:gz') as archive:
                binary = archive.extractfile(tool)
                if binary is None:
                    raise ValueError(f'{tool}: executable is missing')
                executable = directory / tool
                executable.write_bytes(binary.read())
                executable.chmod(0o755)
                LOGGER.info('Installed %s to %s', tool, directory)
        if not os.environ.get('GITHUB_PATH'):
            raise ValueError('GITHUB_PATH is missing')
        with Path(os.environ['GITHUB_PATH']).open('a', encoding='utf-8') as stream:
            stream.write(f'{directory}\n')

    def images(self, resources):
        images = set()
        for resource in resources:
            if not isinstance(resource, dict):
                continue
            kind = resource.get('kind')
            if kind == 'List':
                images.update(self.images(resource.get('items') or []))
                continue
            spec = resource.get('spec') or {}
            if kind in ('Deployment', 'DaemonSet', 'StatefulSet', 'ReplicaSet', 'ReplicationController', 'Job'):
                spec = (spec.get('template') or {}).get('spec') or {}
            elif kind == 'CronJob':
                spec = (((spec.get('jobTemplate') or {}).get('spec') or {}).get('template') or {}).get('spec') or {}
            elif kind != 'Pod':
                continue
            for group in ('containers', 'initContainers', 'ephemeralContainers'):
                for container in spec.get(group) or []:
                    if isinstance(container, dict) and isinstance(container.get('image'), str):
                        images.add(container['image'])
        return sorted(images)

    def render_chart(self, chart):
        """Render a chart with its root values.yaml into dist/render and return the manifest path."""
        name = Path(chart).name
        ci = ChartPipeline(self.root, self.runner, self.pins)
        ci.add_repositories()
        ci.dependencies(chart)
        rendered = ci.run(['helm', 'template', name, chart], capture=True).stdout
        manifest = self.root / 'dist' / 'render' / f'{name}.yaml'
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text(rendered, encoding='utf-8')
        return manifest

    def read_misconfigurations(self, report):
        """Return (severity, id, target, resource, title) tuples from a Trivy JSON report, or [] when it is missing."""
        if not report.is_file():
            return []
        findings = []
        for result in json.loads(report.read_text(encoding='utf-8')).get('Results') or []:
            for item in result.get('Misconfigurations') or []:
                resource = (item.get('CauseMetadata') or {}).get('Resource') or '-'
                findings.append((item.get('Severity', ''), item.get('ID', ''), result.get('Target', ''),
                                 resource, item.get('Title', '')))
        return findings

    def log_misconfigurations(self, name, report):
        """Log each Trivy misconfiguration and add a table to the job summary when running in GitHub Actions."""
        if not report.is_file():
            LOGGER.error('%s: no Trivy report at %s', name, report)
            return
        findings = self.read_misconfigurations(report)
        for severity, identifier, target, resource, title in findings:
            LOGGER.error('%s: %s %s %s %s: %s', name, severity, identifier, target, resource, title)
        summary = os.environ.get('GITHUB_STEP_SUMMARY')
        if not summary:
            return
        lines = [f'### Trivy misconfigurations: {name}', '', '| Severity | ID | Target | Resource | Title |',
                 '| --- | --- | --- | --- | --- |']
        lines.extend(f'| {s} | {i} | {t} | {r} | {ti} |' for s, i, t, r, ti in findings)
        with Path(summary).open('a', encoding='utf-8') as stream:
            stream.write('\n'.join(lines) + '\n\n')

    def exception_file(self, name):
        """Return the per-chart Trivy exception file path as a string, or None when the chart has none."""
        path = self.root / 'security' / 'trivy-exceptions' / f'{name}.yaml'
        return str(path) if path.is_file() else None

    def exception_rows(self, exceptions):
        """Return (category, id, statement) tuples from a Trivy exception file."""
        data = yaml.safe_load(Path(exceptions).read_text(encoding='utf-8')) or {}
        return [(category, entry.get('id', ''), entry.get('statement', ''))
                for category, entries in data.items() for entry in entries or []]

    def log_exceptions(self, name, exceptions):
        """Log the active Trivy exclusions and add them to the job summary, so applied exclusions stay visible."""
        if not exceptions:
            return
        rows = self.exception_rows(exceptions)
        for category, identifier, statement in rows:
            LOGGER.info('%s: exclusion %s %s: %s', name, category, identifier, statement)
        summary = os.environ.get('GITHUB_STEP_SUMMARY')
        if not summary:
            return
        lines = [f'### Trivy exclusions: {name}', '', '| Category | ID | Statement |', '| --- | --- | --- |']
        lines.extend(f'| {c} | {i} | {s} |' for c, i, s in rows)
        with Path(summary).open('a', encoding='utf-8') as stream:
            stream.write('\n'.join(lines) + '\n\n')

    def scan_chart(self, chart):
        chart = Path('charts') / Path(chart).name
        name = chart.name
        LOGGER.info('Scanning chart %s', name)
        metadata = yaml.safe_load((self.root / chart / 'Chart.yaml').read_text(encoding='utf-8'))
        if metadata.get('type') == 'library':
            LOGGER.info('%s: library chart has no standalone renderable manifest', name)
            return
        output = self.root / 'dist' / 'security' / name
        output.mkdir(parents=True, exist_ok=True)
        (output / ERROR_REPORT).unlink(missing_ok=True)
        manifest = self.render_chart(chart)
        arguments = ['trivy', 'config', '--severity', 'HIGH,CRITICAL', '--format', 'json', '--exit-code', '1',
                     '--output', output / 'config.json']
        exceptions = self.exception_file(name)
        self.log_exceptions(name, exceptions)
        if exceptions:
            self.report_excluded_misconfigurations(name, output, manifest, exceptions)
            arguments += ['--ignorefile', exceptions]
        arguments.append(manifest)
        try:
            self.scan(output, 'trivy config', arguments)
        except subprocess.CalledProcessError:
            self.log_misconfigurations(name, output / 'config.json')
            raise
        found = set(self.images(yaml.safe_load_all(manifest.read_text(encoding='utf-8'))))
        (output / 'images.json').write_text(json.dumps(sorted(found), indent=2) + '\n', encoding='utf-8')
        LOGGER.info('%s: scanning %d image(s)', name, len(found))
        if not found:
            LOGGER.info('%s: no images in the rendered default workloads', name)
        failed = []
        for image in sorted(found):
            identifier = hashlib.sha256(image.encode('utf-8')).hexdigest()[:16]
            try:
                self.scan(output, f'trivy image {image}',
                          ['trivy', 'image', '--scanners', 'vuln', '--severity', 'CRITICAL', '--ignore-unfixed',
                           '--format', 'json', '--exit-code', '1', '--output', output / f'image-{identifier}.json',
                           image])
            except subprocess.CalledProcessError:
                failed.append(image)
        self.report_high_vulnerabilities(name, output, found)
        if failed:
            raise RuntimeError(f'{name}: image scans failed for {len(failed)} image(s)')

    def report_high_vulnerabilities(self, name, output, images):
        """Count HIGH image vulnerabilities, log them and add a job summary table without failing the scan."""
        rows = []
        for image in sorted(images):
            identifier = hashlib.sha256(image.encode('utf-8')).hexdigest()[:16]
            report = output / f'image-high-{identifier}.json'
            try:
                self.run(['trivy', 'image', '--scanners', 'vuln', '--severity', 'HIGH', '--ignore-unfixed',
                          '--format', 'json', '--output', report, image])
            except subprocess.CalledProcessError:
                LOGGER.warning('%s: HIGH vulnerability report failed for %s', name, image)
                rows.append((image, 'scan failed'))
                continue
            count = self.count_vulnerabilities(report)
            LOGGER.warning('%s: %d HIGH vulnerabilit%s in %s', name, count, 'y' if count == 1 else 'ies', image)
            rows.append((image, str(count)))
        summary = os.environ.get('GITHUB_STEP_SUMMARY')
        if not summary or not rows:
            return
        lines = [f'### HIGH image vulnerabilities: {name}', '', '| Image | HIGH findings |', '| --- | --- |']
        lines.extend(f'| {image} | {count} |' for image, count in rows)
        with Path(summary).open('a', encoding='utf-8') as stream:
            stream.write('\n'.join(lines) + '\n\n')

    def report_excluded_misconfigurations(self, name, output, manifest, exceptions):
        """Log and summarize the misconfigurations that the exception file suppresses, without failing the scan."""
        report = output / 'config-unfiltered.json'
        try:
            self.run(['trivy', 'config', '--severity', 'HIGH,CRITICAL', '--format', 'json', '--output', report,
                      manifest])
        except subprocess.CalledProcessError:
            LOGGER.warning('%s: unfiltered misconfiguration report failed', name)
            return
        statements = {identifier: statement for _, identifier, statement in self.exception_rows(exceptions)}
        rows = []
        for severity, identifier, target, resource, title in self.read_misconfigurations(report):
            if identifier in statements:
                rows.append((severity, identifier, target, resource, title, statements[identifier]))
        for severity, identifier, target, resource, title, statement in rows:
            LOGGER.warning('%s: excluded %s %s %s %s: %s (%s)', name, severity, identifier, target, resource, title,
                           statement)
        summary = os.environ.get('GITHUB_STEP_SUMMARY')
        if not summary or not rows:
            return
        lines = [f'### Excluded misconfigurations: {name}', '', '| Severity | ID | Target | Resource | Title | Exclusion statement |',
                 '| --- | --- | --- | --- | --- | --- |']
        lines.extend(f'| {s} | {i} | {t} | {r} | {ti} | {st} |' for s, i, t, r, ti, st in rows)
        with Path(summary).open('a', encoding='utf-8') as stream:
            stream.write('\n'.join(lines) + '\n\n')

    def count_vulnerabilities(self, report):
        """Return the number of vulnerabilities in a Trivy JSON report, or 0 when no report was written."""
        if not report.is_file():
            return 0
        results = json.loads(report.read_text(encoding='utf-8')).get('Results') or []
        return sum(len(result.get('Vulnerabilities') or []) for result in results)

    def scan_secrets(self, base=None):
        """Scan git history for secrets, limited to commits after base when a base revision is given."""
        output = self.root / 'dist' / 'security' / 'repository'
        output.mkdir(parents=True, exist_ok=True)
        (output / ERROR_REPORT).unlink(missing_ok=True)
        LOGGER.info('Scanning git history for secrets (base: %s)', base or 'all commits')
        command = ['gitleaks', 'git', '--redact=100', '--exit-code', '0', '--report-format', 'json',
                   '--report-path', output / 'gitleaks.json']
        if base:
            command.append(f'--log-opts={base}..HEAD')
        self.scan(output, 'gitleaks', command + [self.root])

    def audit_dependencies(self):
        """Audit the installed Python packages for known vulnerabilities."""
        output = self.root / 'dist' / 'security' / 'repository'
        output.mkdir(parents=True, exist_ok=True)
        (output / ERROR_REPORT).unlink(missing_ok=True)
        LOGGER.info('Auditing installed Python packages, report: %s', output / 'pip-audit.json')
        report = output / 'pip-audit.json'
        result = self.run([sys.executable, '-m', 'pip_audit', '--format', 'json', '--output', report], check=False)
        if result.returncode:
            if result.returncode != 1 or not report.is_file():
                self.record_error(output, 'pip-audit', f'exit code {result.returncode}')
                raise subprocess.CalledProcessError(result.returncode, result.args)
            try:
                data = json.loads(report.read_text(encoding='utf-8'))
            except (OSError, ValueError) as error:
                self.record_error(output, 'pip-audit', 'report is not valid JSON')
                raise RuntimeError('pip-audit could not write a valid report') from error
            if not isinstance(data, dict) or not any(dependency.get('vulns') for dependency in data.get('dependencies', [])):
                self.record_error(output, 'pip-audit', 'failed without reported vulnerabilities')
                raise RuntimeError('pip-audit failed without reported vulnerabilities')

    def scan_repository(self):
        """Run the full secret scan and dependency audit."""
        self.scan_secrets()
        self.audit_dependencies()


def main():
    parser = argparse.ArgumentParser(description='SpotINFO security scans')
    commands = parser.add_subparsers(dest='command', required=True)
    setup = commands.add_parser('setup-tools')
    setup.add_argument('--directory', required=True)
    setup.add_argument('--tool', choices=list(SECURITY_TOOLS), action='append', required=True)
    commands.add_parser('repository')
    secrets = commands.add_parser('secrets')
    secrets.add_argument('--base', default='', help='scan only commits after this revision')
    commands.add_parser('dependencies')
    chart = commands.add_parser('chart')
    chart.add_argument('chart', nargs='?', default=os.environ.get('CHART'))
    args = parser.parse_args()
    configure_logging()
    if args.command == 'chart' and not args.chart:
        parser.error('chart or CHART is required')
    security = SecurityScanner(Path.cwd())
    if args.command == 'setup-tools':
        security.setup_tools(args.directory, args.tool)
    elif args.command == 'repository':
        security.scan_repository()
    elif args.command == 'secrets':
        security.scan_secrets(args.base or None)
    elif args.command == 'dependencies':
        security.audit_dependencies()
    else:
        security.scan_chart(args.chart)


if __name__ == '__main__':
    main()
