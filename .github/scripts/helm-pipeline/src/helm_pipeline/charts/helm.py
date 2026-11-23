"""Wrap the Helm CLI for chart commands: repositories, dependencies, linting, rendering, and packaging."""

import logging
from pathlib import Path

LOGGER = logging.getLogger(__name__)
HELM_REPOSITORIES = {
    'istio': 'https://istio-release.storage.googleapis.com/charts',
    'prometheus-community': 'https://prometheus-community.github.io/helm-charts',
    'stakater': 'https://stakater.github.io/stakater-charts',
    'csi': 'https://raw.githubusercontent.com/kubernetes-csi/csi-driver-nfs/master/charts',
    'headlamp': 'https://kubernetes-sigs.github.io/headlamp',
    'kubescape': 'https://kubescape.github.io/helm-charts/',
    'argo': 'https://argoproj.github.io/argo-helm',
    'kyverno': 'https://kyverno.github.io/kyverno/',
    'external-secrets': 'https://charts.external-secrets.io',
    'aquasecurity': 'https://aquasecurity.github.io/helm-charts/',
    'cilium': 'https://helm.cilium.io/',
    'metallb': 'https://metallb.github.io/metallb',
    'traefik': 'https://traefik.github.io/charts',
}


class HelmClient:
    """Run Helm commands for charts and manage the Helm repositories they depend on."""

    def __init__(self, commands, catalog):
        """Store the command runner and the chart catalog.

        Args:
            commands: A CommandRunner instance.
            catalog: A ChartCatalog instance.
        """
        self.commands = commands
        self.catalog = catalog

    def add_repositories(self):
        """Register and refresh the Helm repositories that charts depend on."""
        for name, url in HELM_REPOSITORIES.items():
            self.commands.run(['helm', 'repo', 'add', name, url, '--force-update'])
        self.commands.run(['helm', 'repo', 'update'])

    def dependencies(self, chart, cwd=None):
        """Build chart dependencies from Chart.lock, or update them when the lock file is missing."""
        path = Path(chart)
        if not path.is_absolute():
            path = Path(cwd or self.commands.root) / path
        command = 'build' if (path / 'Chart.lock').is_file() else 'update'
        if command == 'update' and self.catalog.metadata(path).get('dependencies'):
            LOGGER.warning('%s: Chart.lock is missing; dependencies are re-resolved', path.name)
        self.commands.run(['helm', 'dependency', command, chart], cwd=cwd)

    def lint(self, chart, values=None):
        """Lint a chart, optionally with a values file."""
        command = ['helm', 'lint', chart]
        if values:
            command += ['--values', values]
        self.commands.run(command)

    def render(self, chart, values, cwd=None):
        """Return the manifests that Helm renders for a chart with the given values file."""
        return self.commands.run([
            'helm', 'template', 'test', chart, '--namespace', 'operators', '--values', values,
        ], cwd=cwd, capture=True).stdout

    def package(self, chart, destination):
        """Package a chart into the destination directory."""
        self.commands.run(['helm', 'package', chart, '--destination', destination])

    def push(self, package, registry):
        """Push a packaged chart to an OCI registry."""
        self.commands.run(['helm', 'push', package, f'oci://{registry}/charts'])

    def registry_login(self, registry, username, password):
        """Log in to an OCI registry, passing the password on standard input."""
        self.commands.run(
            ['helm', 'registry', 'login', registry, '-u', username, '--password-stdin'],
            input_text=password + '\n',
        )

    def show_chart(self, registry, name, version):
        """Return the result of looking up a chart version in a registry without raising on failure."""
        return self.commands.run([
            'helm', 'show', 'chart', f'oci://{registry}/charts/{name}', '--version', version,
        ], capture=True, check=False)

    def plugins_directory(self):
        """Return the Helm plugin directory reported by helm env."""
        plugins = self.commands.run(['helm', 'env', 'HELM_PLUGINS'], capture=True).stdout.strip()
        if not plugins:
            raise ValueError('Helm plugin directory is missing')
        return Path(plugins)
