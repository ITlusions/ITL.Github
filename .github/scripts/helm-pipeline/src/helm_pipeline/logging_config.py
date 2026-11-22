# AI generated code: GitHub Copilot Claude Haiku 5.5
"""Configure logging for the CI scripts so progress messages go to stderr and stdout stays free for data."""

import logging
import os

LOG_FORMAT = '%(asctime)s %(levelname)s %(name)s: %(message)s'


def configure_logging() -> None:
    """Log to stderr at the level named by the LOG_LEVEL environment variable, defaulting to INFO."""
    logging.basicConfig(level=os.environ.get('LOG_LEVEL', 'INFO').upper(), format=LOG_FORMAT)
