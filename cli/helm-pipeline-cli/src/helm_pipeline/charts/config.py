"""Read per-chart .ciconfig settings and write them as GitHub Actions outputs."""

import json
from pathlib import Path

import yaml

from helm_pipeline.charts.kind_config import KindSettingsReader

CONFIG_MARKER = '.ciconfig'
# Optional per-chart settings; a missing key falls back to the reusable workflow input.
CONFIG_KEYS = (
    'timeout-minutes',
    'helm-version',
    'kube-version',
    'kubeconform',
    'values-files',
    'kind-test',
    'kind-values-files',
    'kind-prerequisites',
    'kind-timeout',
    'kind-namespace',
    'trivy',
    'kubescape',
)
SCANNER_KEYS = ('trivy', 'kubescape')
# Placeholder scenario so the workflow matrix is never empty; GitHub rejects an empty matrix.
DISABLED_SCENARIO = 'disabled'


class ChartConfig:
    """Parse a chart's .ciconfig file and expose its settings as workflow outputs."""

    def __init__(self, root, github):
        """Store the repository root and the GitHub output writer.

        Args:
            root: Repository root that contains the charts.
            github: A GitHubFiles instance.
        """
        self.root = Path(root).resolve()
        self.github = github

    def read(self, chart):
        """Return the validated settings of a chart's .ciconfig file, or an empty mapping when it is absent."""
        config = self.load(chart)
        unknown = sorted(set(config) - set(CONFIG_KEYS))
        if unknown:
            raise ValueError(f'{chart}/{CONFIG_MARKER} has unknown key(s): {", ".join(unknown)}')
        values = config.get('values-files', [])
        if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
            raise ValueError(f'{chart}/{CONFIG_MARKER}: values-files must be a list of paths')
        self.kind_settings(chart)
        for scanner in SCANNER_KEYS:
            self.scanner_enabled(chart, scanner)
        return config

    def scanner_enabled(self, chart, scanner):
        """Return whether a security scanner runs for a chart; the scanner is enabled unless .ciconfig sets it to false.

        Args:
            chart: Chart path relative to the repository root.
            scanner: Either trivy or kubescape.
        """
        value = self.load(chart).get(scanner, True)
        if not isinstance(value, bool):
            raise ValueError(f'{chart}/{CONFIG_MARKER}: {scanner} must be true or false')
        return value

    def load(self, chart):
        """Return the parsed .ciconfig mapping of a chart, or an empty mapping when the file is absent."""
        path = self.root / chart / CONFIG_MARKER
        if not path.is_file():
            return {}
        config = yaml.safe_load(path.read_text(encoding='utf-8')) or {}
        if not isinstance(config, dict):
            raise ValueError(f'{chart}/{CONFIG_MARKER} must be a mapping')
        return config

    def kind_settings(self, chart):
        """Return the validated kind-test settings of a chart.

        Args:
            chart: Chart path relative to the repository root.

        Returns:
            A KindSettings instance. Scenarios without their own values use the chart's values-files.
        """
        config = self.load(chart)
        return KindSettingsReader(f'{chart}/{CONFIG_MARKER}').read(config, config.get('values-files', []))

    def write_outputs(self, chart):
        """Write the chart's .ciconfig settings as GitHub Actions outputs; unset settings are empty strings."""
        config = self.read(chart)
        settings = self.kind_settings(chart)
        kubeconform = config.get('kubeconform', '')
        scenario_names = [scenario.name for scenario in settings.scenarios] or [DISABLED_SCENARIO]
        outputs = {
            'timeout-minutes': config.get('timeout-minutes', ''),
            'helm-version': config.get('helm-version', ''),
            'kube-version': config.get('kube-version', ''),
            'kubeconform': str(kubeconform).lower() if kubeconform != '' else '',
            
            'kind-test': str(settings.enabled).lower() if 'kind-test' in config else '',
            'kind-scenarios': json.dumps(scenario_names),
        }
        text = ''.join(f'{key}={value}\n' for key, value in outputs.items())
        values = config.get('values-files', [])
        if values:
            # Multi-line output requires the heredoc syntax of GITHUB_OUTPUT.
            text += 'values-files<<CONFIGCI_EOF\n' + '\n'.join(values) + '\nCONFIGCI_EOF\n'
        else:
            text += 'values-files=\n'
        self.github.emit('GITHUB_OUTPUT', text)

    def security_enabled(self, chart):
        """Return whether at least one security scanner runs for a chart.

        Args:
            chart: Chart path relative to the repository root.
        """
        return self.scanner_enabled(chart, 'trivy') or self.scanner_enabled(chart, 'kubescape')

    def write_security_charts(self, affected):
        """Write the names of the affected charts that run a security scan as the security-charts output.

        Args:
            affected: Chart paths relative to the repository root, such as charts/<name>.
        """
        names = [chart.split('/')[-1] for chart in affected if self.security_enabled(chart)]
        self.github.emit('GITHUB_OUTPUT', f'security-charts={json.dumps(names, separators=(",", ":"))}\n')
