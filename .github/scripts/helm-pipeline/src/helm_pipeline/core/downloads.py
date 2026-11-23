"""Download pinned release files and verify them before they are used."""

import hashlib
import io
import logging
import tarfile
import urllib.request

LOGGER = logging.getLogger(__name__)


class VerifiedDownloader:
    """Download release files and reject any whose SHA-256 digest differs from the pin."""

    def fetch(self, download):
        """Return the bytes of a pinned download after verifying its checksum."""
        LOGGER.info('Downloading %s', download.url)
        with urllib.request.urlopen(download.url, timeout=120) as response:
            data = response.read()
        if hashlib.sha256(data).hexdigest() != download.sha256:
            raise ValueError(f'Checksum does not match: {download.url}')
        LOGGER.info('Checksum verified for %s', download.url)
        return data

    def extract(self, data, destination, members):
        """Extract named regular files from a gzip tar archive into a directory.

        Executables get mode 755; the Helm plugin manifest keeps its default mode.
        """
        destination.mkdir(parents=True, exist_ok=True)
        with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as archive:
            for name in members:
                member = archive.getmember(name)
                if not member.isfile():
                    raise ValueError(f'{name} is not a regular file')
                source = archive.extractfile(member)
                if source is None:
                    raise ValueError(f'{name} is missing from the archive')
                target = destination / name
                target.write_bytes(source.read())
                if name != 'plugin.yaml':
                    target.chmod(0o755)
