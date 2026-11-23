"""Tests for the packaged config.yaml that pins the tool downloads."""

import unittest

from helm_pipeline.core.settings import Download, ToolPins

# AI generated code: GitHub Copilot Claude Haiku 5.5
DIGEST = 'a' * 64


def entry(url='https://example.com/tool.tgz', sha256=DIGEST):
    """Build one tool entry as it appears in config.yaml."""
    return f'    url: {url}\n    sha256: {sha256}\n'


class ToolConfigTest(unittest.TestCase):
    """Behavioral tests for loading and validating config.yaml."""

    def test_packaged_config_pins_all_tools(self):
        """Test that the packaged config.yaml loads every tool the pipelines install."""
        pins = ToolPins.load()
        self.assertEqual(
            pins.names(),
            ['gitleaks', 'helm-unittest', 'kind', 'kubeconform', 'kubectl', 'kubescape', 'trivy'],
        )
        self.assertTrue(pins.get('trivy').url.startswith('https://'))
        self.assertIsInstance(pins.get('kind'), Download)

    def test_valid_entry_is_returned_as_download(self):
        """Test that a well-formed tools mapping yields one Download per tool."""
        text = 'tools:\n  trivy:\n' + entry()
        downloads = ToolPins.parse_tools(text)
        self.assertEqual(downloads['trivy'], Download('https://example.com/tool.tgz', DIGEST))

    def test_unknown_top_level_key_is_rejected(self):
        """Test that config.yaml rejects any top-level key other than tools."""
        with self.assertRaisesRegex(ValueError, 'only the top-level key tools'):
            ToolPins.parse_tools('tools: {}\nother: 1\n')

    def test_missing_tools_key_is_rejected(self):
        """Test that config.yaml without a tools mapping is rejected."""
        with self.assertRaisesRegex(ValueError, 'only the top-level key tools'):
            ToolPins.parse_tools('{}\n')

    def test_entry_missing_a_key_is_rejected(self):
        """Test that each tool needs both url and sha256."""
        with self.assertRaisesRegex(ValueError, 'exactly the keys url and sha256'):
            ToolPins.parse_tools('tools:\n  trivy:\n    url: https://example.com/tool.tgz\n')

    def test_http_url_is_rejected(self):
        """Test that tool downloads must use https."""
        with self.assertRaisesRegex(ValueError, 'must be an https'):
            ToolPins.parse_tools('tools:\n  trivy:\n' + entry(url='http://example.com/tool.tgz'))

    def test_short_digest_is_rejected(self):
        """Test that a sha256 that is not 64 lowercase hexadecimal characters is rejected."""
        with self.assertRaisesRegex(ValueError, 'sha256 must be 64'):
            ToolPins.parse_tools('tools:\n  trivy:\n' + entry(sha256='abc'))

    def test_uppercase_digest_is_rejected(self):
        """Test that the sha256 must be written in lowercase hexadecimal."""
        with self.assertRaisesRegex(ValueError, 'sha256 must be 64'):
            ToolPins.parse_tools('tools:\n  trivy:\n' + entry(sha256='A' * 64))


if __name__ == '__main__':
    unittest.main()
