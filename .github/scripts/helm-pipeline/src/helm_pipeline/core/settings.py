"""Resolve the pinned tool downloads from the config.yaml file packaged with helm_pipeline."""

import re
from dataclasses import dataclass
from importlib import resources

import yaml

# AI generated code: GitHub Copilot Claude Haiku 5.5
CONFIG_FILE = 'config.yaml'
DIGEST_PATTERN = re.compile(r'[0-9a-f]{64}')


@dataclass(frozen=True)
class Download:
    """Hold the URL and the expected SHA-256 digest of one tool release."""

    url: str
    sha256: str


class ToolPins:
    """Map each pinned tool name to the download URL and SHA-256 digest that the CI uses."""

    def __init__(self, downloads):
        """Store the resolved downloads keyed by tool name.

        Args:
            downloads: Mapping of tool name to Download.
        """
        self.downloads = dict(downloads)

    @classmethod
    def load(cls):
        """Return the pins from the config.yaml packaged with helm_pipeline.

        Returns:
            The ToolPins read from the packaged config file.
        """
        text = resources.files('helm_pipeline').joinpath(CONFIG_FILE).read_text(encoding='utf-8')
        return cls(cls.parse_tools(text))

    @classmethod
    def parse_tools(cls, text):
        """Validate the YAML text of a config file and return its downloads.

        Args:
            text: YAML text with a single top-level key, tools, that maps tool names to url and sha256 entries.

        Returns:
            A dictionary of tool name to Download.

        Raises:
            ValueError: When the text has unknown keys, a missing tools mapping, or invalid url or sha256 values.
        """
        data = yaml.safe_load(text) or {}
        if not isinstance(data, dict) or set(data) != {'tools'}:
            raise ValueError(f'{CONFIG_FILE}: only the top-level key tools is supported')
        tools = data['tools']
        if not isinstance(tools, dict):
            raise ValueError(f'{CONFIG_FILE}: tools must be a mapping of tool names to url and sha256')
        return {name: cls.parse_entry(name, entry) for name, entry in tools.items()}

    @classmethod
    def parse_entry(cls, name, entry):
        """Validate one tool entry and return it as a Download.

        Args:
            name: Tool name, used in error messages.
            entry: The mapping that holds url and sha256.

        Returns:
            The validated Download.

        Raises:
            ValueError: When the entry lacks url or sha256, or when either value is malformed.
        """
        if not isinstance(entry, dict) or set(entry) != {'url', 'sha256'}:
            raise ValueError(f'{CONFIG_FILE}: tool {name} needs exactly the keys url and sha256')
        url = entry['url']
        digest = entry['sha256']
        if not isinstance(url, str) or not url.startswith('https://'):
            raise ValueError(f'{CONFIG_FILE}: tool {name} url must be an https:// address')
        if not isinstance(digest, str) or not DIGEST_PATTERN.fullmatch(digest):
            raise ValueError(f'{CONFIG_FILE}: tool {name} sha256 must be 64 lowercase hexadecimal characters')
        return Download(url, digest)

    def names(self):
        """Return the sorted names of all pinned tools."""
        return sorted(self.downloads)

    def get(self, name):
        """Return the download pinned for a tool.

        Args:
            name: Tool name such as trivy or kind.

        Returns:
            The Download with its URL and SHA-256 digest.
        """
        return self.downloads[name]
