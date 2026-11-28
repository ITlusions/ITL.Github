"""Install the pinned security scanners into a directory and add it to PATH."""

from pathlib import Path




class SecurityToolInstaller:
    """Install pinned gitleaks and Trivy binaries for the security jobs."""

    TOOLS = ('gitleaks', 'kubescape', 'trivy')

    def __init__(self, installer, github, pins):
        """Store the collaborators used to install binaries and edit PATH.

        Args:
            installer: A ToolInstaller instance.
            github: A GitHubFiles instance.
            pins: A ToolPins instance that resolves the download for each tool.
        """
        self.installer = installer
        self.github = github
        self.pins = pins

    def setup_tools(self, directory, tools):
        """Install each named tool into the directory, then add the directory to PATH.

        Args:
            directory: Installation directory.
            tools: Names of the tools to install, each one of TOOLS.
        """
        directory = Path(directory).resolve()
        directory.mkdir(parents=True, exist_ok=True)
        for tool in tools:
            self.installer.install_archive(self.pins.get(tool), directory, (tool,), tool)
        self.github.add_to_path(directory)
