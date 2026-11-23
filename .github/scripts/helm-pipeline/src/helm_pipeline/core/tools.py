"""Install pinned tool binaries into a directory, reusing binaries that are already present."""

import logging

LOGGER = logging.getLogger(__name__)


class ToolInstaller:
    """Install pinned tools, skipping any binary that a CI cache already restored."""

    def __init__(self, downloader):
        """Store the downloader that fetches and verifies pinned files.

        Args:
            downloader: A VerifiedDownloader instance.
        """
        self.downloader = downloader

    def install_archive(self, download, destination, members, binary):
        """Extract members from a pinned archive unless the binary already exists in the destination."""
        if (destination / binary).is_file():
            LOGGER.info('Reusing cached %s in %s', binary, destination)
            return
        self.downloader.extract(self.downloader.fetch(download), destination, members)

    def install_binary(self, download, destination, name):
        """Write a pinned single-file binary into the destination unless it already exists."""
        binary = destination / name
        if binary.is_file():
            LOGGER.info('Reusing cached %s in %s', name, destination)
            return
        binary.write_bytes(self.downloader.fetch(download))
        binary.chmod(0o755)
