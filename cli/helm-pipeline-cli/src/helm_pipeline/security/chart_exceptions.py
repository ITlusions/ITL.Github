"""Read the per-chart exception file that suppresses known findings for Trivy and Kubescape."""

import json
import logging
from datetime import date
from pathlib import Path

import yaml

LOGGER = logging.getLogger(__name__)

TRIVY_IGNORE_FILE = 'trivy-ignore.yaml'
KUBESCAPE_EXCEPTION_FILE = 'kubescape-exceptions.json'
EXCEPTION_FILE_NAMES = ('exceptions.yaml', 'exceptions.yml', 'exceptions.json')
METADATA_FIELDS = ('owner', 'expires', 'request')
EXCLUSION_HEADERS = ['Scanner', 'ID', 'Detail', 'Owner', 'Expires', 'Request', 'Status']
STATUS_ACTIVE = 'active'
STATUS_EXPIRED = 'expired'


class ChartExceptions:
    """Locate and split the exception file of a chart into the Trivy and Kubescape inputs."""

    def __init__(self, root, github, today=None, verifier=None):
        """Store the repository root, the GitHub file writer and the date used to judge expiry.

        Args:
            root: Repository root that contains the security directory.
            github: A GitHubFiles instance.
            today: Date that exclusions are compared against; defaults to the current date.
            verifier: An ExceptionSignatureVerifier that must accept each file, or None to skip verification.
        """
        self.root = Path(root)
        self.github = github
        self.today = today or date.today()
        self.verifier = verifier

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
        if self.verifier is not None:
            self.verifier.verify(path)
        return yaml.safe_load(path.read_text(encoding='utf-8')) or {}

    def applied_trivy(self, name):
        """Return the Trivy section without expired exclusions and without the metadata fields."""
        section = {}
        for category, entries in (self.load(name).get('trivy') or {}).items():
            kept = []
            for entry in entries or []:
                if self.is_applied('trivy', entry, entry.get('id', '')):
                    kept.append(self.without_metadata(entry))
            if kept:
                section[category] = kept
        return section

    def applied_kubescape(self, name):
        """Return the Kubescape exceptions without expired exclusions and without the metadata fields."""
        kept = []
        for entry in self.load(name).get('kubescape') or []:
            if self.is_applied('kubescape', entry, entry.get('name', '')):
                kept.append(self.without_metadata(entry))
        return kept

    def trivy_ignorefile(self, name, output):
        """Write the applied Trivy exclusions as an ignore file and return its path, or None when none apply."""
        section = self.applied_trivy(name)
        if not section:
            return None
        path = output / TRIVY_IGNORE_FILE
        path.write_text(yaml.safe_dump(section, sort_keys=False), encoding='utf-8')
        return str(path)

    def kubescape_exception_file(self, name, output):
        """Write the applied Kubescape exceptions as JSON and return its path, or None when none apply."""
        section = self.applied_kubescape(name)
        if not section:
            return None
        path = output / KUBESCAPE_EXCEPTION_FILE
        path.write_text(json.dumps(section, indent=2) + '\n', encoding='utf-8')
        return str(path)

    def exclusions(self, name):
        """Return one row per exclusion of a chart with its owner, expiry, request and status."""
        section = self.load(name)
        rows = []
        for entries in (section.get('trivy') or {}).values():
            for entry in entries or []:
                rows.append(self.describe('trivy', entry, entry.get('id', ''), entry.get('statement', '')))
        for entry in section.get('kubescape') or []:
            controls = [policy.get('controlID', '') for policy in entry.get('posturePolicies') or []]
            rows.append(self.describe('kubescape', entry, ', '.join(controls), entry.get('name', '')))
        return rows

    def describe(self, scanner, entry, identifier, detail):
        """Return one exclusion as a dictionary with its status relative to the reference date."""
        expires = self.expiry(scanner, entry, identifier)
        status = STATUS_ACTIVE if expires >= self.today else STATUS_EXPIRED
        return {
            'scanner': scanner,
            'id': identifier,
            'detail': detail,
            'owner': str(entry['owner']),
            'expires': expires.isoformat(),
            'request': str(entry['request']),
            'status': status,
        }

    def expiry(self, scanner, entry, identifier):
        """Return the expiry date of an exclusion and fail when its owner, expiry or request is missing or invalid."""
        missing = [field for field in METADATA_FIELDS if not entry.get(field)]
        if missing:
            raise RuntimeError(f'{scanner} exclusion {identifier!r} is missing: {", ".join(missing)}')
        try:
            return date.fromisoformat(str(entry['expires']))
        except ValueError as error:
            raise RuntimeError(
                f'{scanner} exclusion {identifier!r} has an invalid expires date: {entry["expires"]}'
            ) from error

    def is_applied(self, scanner, entry, identifier):
        """Return True when the exclusion has not passed its expiry date."""
        return self.expiry(scanner, entry, identifier) >= self.today

    @staticmethod
    def without_metadata(entry):
        """Return a copy of an exclusion without the owner, expiry and request fields that the scanners do not read."""
        return {key: value for key, value in entry.items() if key not in METADATA_FIELDS}

    def trivy_statements(self, name):
        """Return the exclusion statement of each applied Trivy misconfiguration ID for a chart."""
        statements = {}
        for row in self.exclusions(name):
            if row['scanner'] == 'trivy' and row['status'] == STATUS_ACTIVE:
                statements[row['id']] = row['detail']
        return statements

    def log(self, name):
        """Log each exclusion, warn about expired ones, and add all exclusions to the job summary."""
        table = []
        for row in self.exclusions(name):
            if row['status'] == STATUS_EXPIRED:
                LOGGER.warning('%s: %s exclusion %s expired on %s and no longer applies',
                               name, row['scanner'], row['id'], row['expires'])
            else:
                LOGGER.info('%s: %s exclusion %s until %s (owner %s, request %s)',
                            name, row['scanner'], row['id'], row['expires'], row['owner'], row['request'])
            table.append((row['scanner'], row['id'], row['detail'], row['owner'], row['expires'], row['request'],
                          row['status']))
        if table:
            self.github.append_table(f'Exclusions: {name}', EXCLUSION_HEADERS, table)
