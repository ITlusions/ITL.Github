"""Run external commands from the repository root."""

import logging
import subprocess
from pathlib import Path

LOGGER = logging.getLogger(__name__)


class CommandRunner:
    """Run external commands, using the repository root as the default working directory."""

    def __init__(self, root, runner=subprocess.run):
        """Store the repository root and the function that executes commands.

        Args:
            root: Repository root used as the default working directory.
            runner: Callable with the same signature as subprocess.run.
        """
        self.root = Path(root).resolve()
        self.runner = runner

    def run(self, args, *, cwd=None, capture=False, check=True, input_text=None):
        """Run a command and return its completed process."""
        command = [str(arg) for arg in args]
        LOGGER.info('Running %s', ' '.join(command))
        return self.runner(
            command, cwd=cwd or self.root, check=check,
            text=True, encoding='utf-8', capture_output=capture, input=input_text,
        )
