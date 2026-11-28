"""Render a chart with its default values into a manifest for the security scans."""

from pathlib import Path




class ChartRenderer:
    """Render charts with their default values into manifests under dist/render."""

    def __init__(self, commands, helm):
        """Store the command runner and the Helm client.

        Args:
            commands: A CommandRunner instance rooted at the repository.
            helm: A HelmClient instance.
        """
        self.commands = commands
        self.helm = helm

    def render(self, chart):
        """Update dependencies, render the chart, and write the manifest.

        Args:
            chart: Chart path relative to the repository root, such as charts/name.

        Returns:
            Path to the rendered manifest.
        """
        name = Path(chart).name
        self.helm.add_repositories()
        self.helm.dependencies(chart)
        rendered = self.commands.run(['helm', 'template', name, chart], capture=True).stdout
        manifest = self.commands.root / 'dist' / 'render' / f'{name}.yaml'
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text(rendered, encoding='utf-8')
        return manifest
