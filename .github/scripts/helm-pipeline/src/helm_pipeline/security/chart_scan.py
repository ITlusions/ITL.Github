"""Scan one chart's rendered manifests for misconfigurations and container image vulnerabilities."""

import json
import logging
import subprocess
from pathlib import Path

import yaml

from helm_pipeline.security.reports import ScanReport

LOGGER = logging.getLogger(__name__)
# AI generated code: GitHub Copilot Claude Haiku 5.5


class ChartScanner:
    """Render a chart, then run the configuration and image scans against its output."""

    def __init__(self, root, config, renderer, trivy, kubescape, exceptions, misconfigurations, finder):
        """Store the collaborators used to scan one chart.

        Args:
            root: Repository root that contains the charts directory.
            config: A ChartConfig instance that reports which scanners a chart enables.
            renderer: A ChartRenderer instance.
            trivy: A TrivyScanner instance.
            kubescape: A KubescapeScanner instance.
            exceptions: A ChartExceptions instance.
            misconfigurations: A MisconfigurationReport instance.
            finder: An ImageFinder instance.
        """
        self.root = Path(root)
        self.config = config
        self.renderer = renderer
        self.trivy = trivy
        self.kubescape = kubescape
        self.exceptions = exceptions
        self.misconfigurations = misconfigurations
        self.finder = finder

    def scan(self, chart):
        """Scan a chart and raise when a blocking misconfiguration or image scan fails.

        Args:
            chart: Chart name or path; only the final path segment is used.

        Raises:
            subprocess.CalledProcessError: When the configuration scan finds blocking misconfigurations.
            RuntimeError: When one or more image scans fail.
        """
        chart = Path('charts') / Path(chart).name
        name = chart.name
        LOGGER.info('Scanning chart %s', name)
        metadata = yaml.safe_load((self.root / chart / 'Chart.yaml').read_text(encoding='utf-8'))
        if metadata.get('type') == 'library':
            LOGGER.info('%s: library chart has no standalone renderable manifest', name)
            return
        trivy_enabled = self.config.scanner_enabled(chart, 'trivy')
        kubescape_enabled = self.config.scanner_enabled(chart, 'kubescape')
        if not trivy_enabled and not kubescape_enabled:
            LOGGER.info('%s: trivy and kubescape are disabled in .ciconfig; nothing to scan', name)
            return
        output = self.root / 'dist' / 'security' / name
        output.mkdir(parents=True, exist_ok=True)
        self.exceptions.log(name)
        scan_report = ScanReport(output)
        scan_report.clear()
        manifest = self.renderer.render(chart)
        if trivy_enabled:
            self.trivy_config_scan(name, scan_report, manifest, output)
        if kubescape_enabled:
            kubescape_exceptionfile = self.exceptions.kubescape_exception_file(name, output)
            self.kubescape.scan(scan_report, manifest, output, kubescape_exceptionfile)
        if trivy_enabled:
            self.trivy_image_scan(name, scan_report, manifest, output)

    def trivy_config_scan(self, name, scan_report, manifest, output):
        """Run the Trivy configuration scan, honoring the chart's Trivy exception file."""
        trivy_ignorefile = self.exceptions.trivy_ignorefile(name, output)
        if trivy_ignorefile:
            self.report_excluded(name, output, manifest)
        try:
            self.trivy.config_scan(scan_report, manifest, output, trivy_ignorefile)
        except subprocess.CalledProcessError:
            self.misconfigurations.log(name, output / 'config.json')
            raise

    def trivy_image_scan(self, name, scan_report, manifest, output):
        """Scan every container image in the rendered manifest and fail when any image scan fails."""
        resources = yaml.safe_load_all(manifest.read_text(encoding='utf-8'))
        images = self.finder.find(resources)
        (output / 'images.json').write_text(json.dumps(images, indent=2) + '\n', encoding='utf-8')
        LOGGER.info('%s: scanning %d image(s)', name, len(images))
        failed = []
        for image in images:
            try:
                self.trivy.image_scan(scan_report, image, output)
            except subprocess.CalledProcessError:
                failed.append(image)
        self.trivy.high_report(name, output, images)
        if failed:
            raise RuntimeError(f'{name}: image scans failed for {len(failed)} image(s)')

    def report_excluded(self, name, output, manifest):
        """List the findings that the exception file suppresses; a failure here does not stop the scan."""
        report_file = output / 'config-unfiltered.json'
        try:
            self.trivy.unfiltered_config(report_file, manifest)
        except subprocess.CalledProcessError:
            LOGGER.warning('%s: unfiltered misconfiguration report failed', name)
            return
        self.misconfigurations.log_excluded(name, report_file, self.exceptions.trivy_statements(name))
