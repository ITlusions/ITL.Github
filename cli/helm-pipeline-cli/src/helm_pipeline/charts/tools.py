"""Install the CI tools that chart validation needs: kubeconform, the Helm unittest plugin, and kind tooling."""

from pathlib import Path


class ChartToolInstaller:
    """Install pinned chart-validation tools and add them to the workflow PATH."""

    def __init__(self, installer, helm, github, pins):
        """Store the collaborators used to install binaries, read the Helm plugin directory, and edit PATH.

        Args:
            installer: A ToolInstaller instance.
            helm: A HelmClient instance.
            github: A GitHubFiles instance.
            pins: A ToolPins instance that resolves the download for each tool.
        """
        self.installer = installer
        self.helm = helm
        self.github = github
        self.pins = pins

    def setup_tools(self, directory):
        """Install kubeconform and the Helm unittest plugin, then add the directory to PATH."""
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        self.installer.install_archive(self.pins.get('kubeconform'), directory, ('kubeconform',), 'kubeconform')
        self.github.add_to_path(directory)
        unittest_directory = self.helm.plugins_directory() / 'unittest'
        self.installer.install_archive(
            self.pins.get('helm-unittest'), unittest_directory, ('plugin.yaml', 'untt-linux-amd64'), 'untt-linux-amd64',
        )

    def setup_kind(self, directory):
        """Install the pinned kind and kubectl binaries, then add the directory to PATH."""
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        self.github.add_to_path(directory)
        for name in ('kind', 'kubectl'):
            self.installer.install_binary(self.pins.get(name), directory, name)
