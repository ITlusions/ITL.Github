"""Read the per-chart exception file that suppresses known findings for Trivy and Kubescape."""

import json
import logging
from pathlib import Path

import yaml

LOGGER = logging.getLogger(__name__)
# AI generated code: GitHub Copilot Claude Haiku 5.5
TRIVY_IGNORE_FILE = 'trivy-ignore.yaml'
KUBESCAPE_EXCEPTION_FILE = 'kubescape-exceptions.json'
EXCEPTION_FILE_NAMES = ('exceptions.yaml', 'exceptions.yml', 'exceptions.json')


class ChartExceptions:
    """Locate and split the exception file of a chart into the Trivy and Kubescape inputs."""

    def __init__(self, root, github):
        """Store the repository root and the GitHub file writer for job summaries.

        Args:
            root: Repository root that contains the security directory.
            github: A GitHubFiles instance.
        """
        self.root = Path(root)
        self.github = github

    def path_for(self, name):
        """Return the exception file of a chart from its root or the security folder, or None when it has none."""
        candidates = [self.root / 'charts' / name / file_name for file_name in EXCEPTION_FILE_NAMES]
        candidates.append(self.root / 'security' / 'exceptions' / f'{name}.yaml')
        found = [path for path in candidates if path.is_file()]
        if len(found) > 1:
            raise RuntimeError(f'{name}: more than one exception file found: {found}')
        return found[0] if found else None

    def load(self, name):
        """Return the parsed exception file of a chart, or an empty mapping when the chart has none."""
        path = self.path_for(name)
        if path is None:
            return {}
        return yaml.safe_load(path.read_text(encoding='utf-8')) or {}

    def trivy_ignorefile(self, name, output):
        """Write the Trivy section as an ignore file in the report directory and return its path, or None."""
        section = self.load(name).get('trivy')
        if not section:
            return None
        path = output / TRIVY_IGNORE_FILE
        path.write_text(yaml.safe_dump(section, sort_keys=False), encoding='utf-8')
        return str(path)

    def kubescape_exception_file(self, name, output):
        """Write the Kubescape section as JSON in the report directory and return its path, or None."""
        section = self.load(name).get('kubescape')
        if not section:
            return None
        path = output / KUBESCAPE_EXCEPTION_FILE
        path.write_text(json.dumps(section, indent=2) + '\n', encoding='utf-8')
        return str(path)

    def trivy_rows(self, name):
        """Return (category, id, statement) tuples from the Trivy section of a chart."""
        rows = []
        for category, entries in (self.load(name).get('trivy') or {}).items():
            for entry in entries or []:
                rows.append((category, entry.get('id', ''), entry.get('statement', '')))
        return rows

    def trivy_statements(self, name):
        """Return the exclusion statement of each Trivy misconfiguration ID suppressed for a chart."""
        return {identifier: statement for _, identifier, statement in self.trivy_rows(name)}

    def log(self, name):
        """Log the active Trivy exclusions and add them to the job summary so applied exclusions stay visible."""
        rows = self.trivy_rows(name)
        for category, identifier, statement in rows:
            LOGGER.info('%s: exclusion %s %s: %s', name, category, identifier, statement)
        self.github.append_table(f'Trivy exclusions: {name}', ['Category', 'ID', 'Statement'], rows)
