"""Tests for the optional cosign verification of chart exception files."""

import tempfile
import unittest
from pathlib import Path

from helm_pipeline.security.chart_exceptions import ChartExceptions
from helm_pipeline.security.exception_signature import ExceptionSignatureVerifier
from case import test_case


UNSIGNED_EXCEPTIONS = "trivy:\n  misconfigurations: []\n"


class ExceptionSignatureVerifierTest(unittest.TestCase):
    """Behavioral tests for verifying exception files against their sigstore bundles."""

    def write_exception_file(self, root, content=UNSIGNED_EXCEPTIONS):
        """Write the exception file of the demo chart below the repository root and return its path."""
        folder = root / 'security' / 'exceptions'
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / 'demo.yaml'
        path.write_text(content, encoding='utf-8')
        return path

    @test_case('TC-SIG-001', 'The sigstore bundle is named after the exception file it signs')
    def test_bundle_sits_next_to_the_exception_file(self):
        """Test that the sigstore bundle is named after the exception file it signs."""
        self.assertEqual(
            ExceptionSignatureVerifier.bundle_for(Path('security/exceptions/demo.yaml')),
            Path('security/exceptions/demo.yaml.sigstore.json'),
        )

    @test_case('TC-SIG-002', 'An exception file without a signature bundle is never loaded when verification is enabled')
    def test_exception_file_without_bundle_is_rejected(self):
        """Test that an exception file without a signature bundle is never loaded when verification is enabled."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            self.write_exception_file(root)
            exceptions = ChartExceptions(root, None, verifier=ExceptionSignatureVerifier())
            with self.assertRaisesRegex(RuntimeError, 'no signature bundle demo.yaml.sigstore.json'):
                exceptions.load('demo')

    @test_case('TC-SIG-003', 'Exception files load without any signature check when verification is not enabled')
    def test_unsigned_exception_file_loads_when_verification_is_off(self):
        """Test that exception files load without any signature check when verification is not enabled."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            self.write_exception_file(root)
            exceptions = ChartExceptions(root, None)
            self.assertEqual(exceptions.load('demo'), {'trivy': {'misconfigurations': []}})
