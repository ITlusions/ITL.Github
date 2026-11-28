"""Record scanner failures in a report directory so the job summary can list them."""

import json
import logging
import subprocess
from pathlib import Path

LOGGER = logging.getLogger(__name__)

ERROR_REPORT = 'scan-errors.json'


class ScanReport:
    """Hold the report directory of one scan and record the scanners that failed in it."""

    def __init__(self, directory):
        """Store the directory that receives the scan output.

        Args:
            directory: Report directory for one scan target.
        """
        self.directory = Path(directory)

    def clear(self):
        """Remove the error list left behind by an earlier run in the same directory."""
        (self.directory / ERROR_REPORT).unlink(missing_ok=True)

    def record_error(self, scanner, message):
        """Append a failed scanner to the error list in the report directory.

        Args:
            scanner: Name of the scanner that failed.
            message: Reason the scanner failed.
        """
        LOGGER.error('%s failed: %s', scanner, message)
        path = self.directory / ERROR_REPORT
        path.parent.mkdir(parents=True, exist_ok=True)
        errors = json.loads(path.read_text(encoding='utf-8')) if path.is_file() else []
        errors.append({'scanner': scanner, 'message': message})
        path.write_text(json.dumps(errors, indent=2) + '\n', encoding='utf-8')

    def run(self, commands, scanner, args):
        """Run a scanner command and record its failure before re-raising the error.

        Args:
            commands: A CommandRunner instance.
            scanner: Name under which a failure is recorded.
            args: Command and arguments to run.

        Returns:
            The completed process when the command succeeds.
        """
        try:
            return commands.run(args)
        except subprocess.CalledProcessError as error:
            self.record_error(scanner, f'exited with code {error.returncode}; see the findings above')
            raise
