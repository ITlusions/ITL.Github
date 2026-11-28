"""Verify the cosign signature bundle of a chart exception file before its exclusions are applied."""

import subprocess
from pathlib import Path

SIGNATURE_SUFFIX = '.sigstore.json'
OIDC_ISSUER = 'https://token.actions.githubusercontent.com'
DEFAULT_SIGNER_IDENTITY = '^https://github.com/ITlusions/'




class ExceptionSignatureVerifier:
    """Check an exception file against its sigstore bundle and fail when the signature does not match."""

    def __init__(self, identity=DEFAULT_SIGNER_IDENTITY, runner=subprocess.run):
        """Store the signer identity pattern and the process runner used to call cosign.

        Args:
            identity: Regular expression that the signing certificate identity must match.
            runner: Callable that runs processes; subprocess.run when omitted.
        """
        self.identity = identity
        self.runner = runner

    @staticmethod
    def bundle_for(path):
        """Return the sigstore bundle path that sits next to an exception file."""
        path = Path(path)
        return path.with_name(path.name + SIGNATURE_SUFFIX)

    def verify(self, path):
        """Raise when the exception file has no bundle or the bundle does not verify.

        Args:
            path: Exception file to verify.

        Raises:
            RuntimeError: When the bundle is missing or cosign rejects the signature.
        """
        path = Path(path)
        bundle = self.bundle_for(path)
        if not bundle.is_file():
            raise RuntimeError(f'{path.name}: no signature bundle {bundle.name}; its exclusions are not applied')
        result = self.runner(
            ['cosign', 'verify-blob',
             '--bundle', str(bundle),
             '--certificate-identity-regexp', self.identity,
             '--certificate-oidc-issuer', OIDC_ISSUER,
             str(path)],
            capture_output=True, text=True, check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(f'{path.name}: signature verification failed: {result.stderr.strip()}')
