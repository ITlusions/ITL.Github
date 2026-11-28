"""Validate the kind-* settings of a chart's .ciconfig file and convert them into typed settings."""

import re
from dataclasses import dataclass

DEFAULT_NAMESPACE = 'ci-test'
DEFAULT_TIMEOUT_MINUTES = 5
DEFAULT_SCENARIO = 'default'
MAX_NAME_LENGTH = 63
NAME_PATTERN = re.compile(r'[a-z0-9]([-a-z0-9]*[a-z0-9])?')
SCENARIO_KEYS = ('name', 'values-files')
PREREQUISITE_KEYS = ('name', 'namespace', 'chart', 'repo', 'version', 'values-files', 'manifests')
CHART_ONLY_KEYS = ('namespace', 'repo', 'version', 'values-files')


@dataclass(frozen=True)
class KindScenario:
    """One named value set that is installed into its own kind cluster.

    Attributes:
        name: Scenario name, unique within the chart.
        values_files: Values files passed to the chart install.
    """

    name: str
    values_files: tuple


@dataclass(frozen=True)
class KindPrerequisite:
    """One chart or manifest set installed into the kind cluster before the chart under test.

    Attributes:
        name: Release name for charts, or identifier for manifests.
        namespace: Namespace of the chart release; empty for manifests.
        chart: Chart name or path; empty for manifests.
        repo: Helm repository URL or alias; empty when unset.
        version: Chart version; empty when unset.
        values_files: Values files passed to the chart install.
        manifests: Path to a manifest file or directory applied with kubectl; empty for charts.
    """

    name: str
    namespace: str
    chart: str
    repo: str
    version: str
    values_files: tuple
    manifests: str


@dataclass(frozen=True)
class KindSettings:
    """The validated kind-test settings of one chart.

    Attributes:
        enabled: Whether kind tests run for the chart.
        scenarios: Configured scenarios, each installed into its own cluster.
        prerequisites: Charts or manifests installed before the chart under test.
        namespace: Namespace of the chart under test.
        timeout_minutes: Timeout for waiting on installs.
    """

    enabled: bool
    scenarios: tuple
    prerequisites: tuple
    namespace: str
    timeout_minutes: int

    def scenario(self, name):
        """Return the scenario with the given name.

        Args:
            name: Scenario name to look up.

        Returns:
            The matching KindScenario.

        Raises:
            ValueError: When no scenario has that name.
        """
        for scenario in self.scenarios:
            if scenario.name == name:
                return scenario
        raise ValueError(f'kind-test scenario {name} is not configured')



class KindSettingsReader:
    """Validate the kind-* keys of one .ciconfig mapping and convert them into KindSettings."""

    def __init__(self, label):
        """Store the file label used in validation errors.

        Args:
            label: Chart and file name, such as charts/demo/.ciconfig.
        """
        self.label = label

    def read(self, config, default_values=()):
        """Return the validated kind settings of a .ciconfig mapping.

        Args:
            config: The parsed .ciconfig mapping.
            default_values: Values files used when neither kind-values-files nor a scenario sets its own.

        Returns:
            A KindSettings instance.

        Raises:
            ValueError: When any kind-* setting is invalid.
        """
        namespace = self.name(config.get('kind-namespace', DEFAULT_NAMESPACE), 'kind-namespace')
        timeout = self.timeout(config)
        values = self.paths(config, 'kind-values-files') or tuple(default_values)
        scenarios = self.scenarios(config.get('kind-test', False), values)
        prerequisites = self.prerequisites(config.get('kind-prerequisites', []), namespace)
        return KindSettings(bool(scenarios), scenarios, prerequisites, namespace, timeout)

    def error(self, message):
        """Build a ValueError that names the file being validated.

        Args:
            message: Description of the invalid setting.

        Returns:
            A ValueError ready to raise.
        """
        return ValueError(f'{self.label}: {message}')

    def timeout(self, config):
        """Return the kind-timeout setting in minutes."""
        value = config.get('kind-timeout', DEFAULT_TIMEOUT_MINUTES)
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise self.error('kind-timeout must be a positive whole number of minutes')
        return value

    def scenarios(self, value, values):
        """Return the scenarios from a kind-test value, which is true, false, or a list of named scenarios."""
        if isinstance(value, bool):
            return (KindScenario(DEFAULT_SCENARIO, values),) if value else ()
        if not isinstance(value, list) or not value:
            raise self.error('kind-test must be true, false, or a non-empty list of named scenarios')
        scenarios = tuple(self.scenario(item, values) for item in value)
        self.reject_duplicates([scenario.name for scenario in scenarios], 'kind-test scenario')
        return scenarios

    def scenario(self, item, values):
        """Return one named scenario from a kind-test list entry."""
        if not isinstance(item, dict) or 'name' not in item:
            raise self.error('each kind-test scenario must be a mapping with a name')
        self.reject_unknown(item, SCENARIO_KEYS, 'kind-test scenario')
        name = self.name(item['name'], 'kind-test scenario name')
        return KindScenario(name, self.paths(item, 'values-files') or values)

    def prerequisites(self, items, namespace):
        """Return the kind-prerequisites entries."""
        if not isinstance(items, list):
            raise self.error('kind-prerequisites must be a list')
        prerequisites = tuple(self.prerequisite(item, namespace) for item in items)
        self.reject_duplicates([prerequisite.name for prerequisite in prerequisites], 'kind-prerequisites name')
        return prerequisites

    def prerequisite(self, item, namespace):
        """Return one prerequisite entry, which is either a chart or a manifest set."""
        if not isinstance(item, dict) or 'name' not in item:
            raise self.error('each kind-prerequisites entry must be a mapping with a name')
        self.reject_unknown(item, PREREQUISITE_KEYS, 'kind-prerequisites entry')
        name = self.name(item['name'], 'kind-prerequisites name')
        if ('chart' in item) == ('manifests' in item):
            raise self.error(f'kind-prerequisites {name} needs exactly one of chart or manifests')
        if 'manifests' in item:
            self.reject_keys(item, CHART_ONLY_KEYS, f'kind-prerequisites {name} with manifests')
            return KindPrerequisite(name, '', '', '', '', (), self.text(item, 'manifests', name))
        return KindPrerequisite(
            name=name,
            namespace=self.name(item.get('namespace', namespace), 'kind-prerequisites namespace'),
            chart=self.text(item, 'chart', name),
            repo=self.optional_text(item, 'repo', name),
            version=self.optional_text(item, 'version', name),
            values_files=self.paths(item, 'values-files'),
            manifests='',
        )

    def name(self, value, what):
        """Return a DNS-label style name such as a scenario, namespace, or release name."""
        if not isinstance(value, str) or len(value) > MAX_NAME_LENGTH or not NAME_PATTERN.fullmatch(value):
            raise self.error(f'{what} must be lowercase letters, digits, and hyphens, at most {MAX_NAME_LENGTH} characters')
        return value

    def text(self, item, key, owner):
        """Return a required non-empty string value."""
        value = item.get(key)
        if not isinstance(value, str) or not value:
            raise self.error(f'{owner} needs a non-empty {key}')
        return value

    def optional_text(self, item, key, owner):
        """Return an optional string value, or an empty string when the key is absent."""
        if key not in item:
            return ''
        return self.text(item, key, owner)

    def paths(self, mapping, key):
        """Return a list of path strings stored under the key, or an empty tuple when absent."""
        value = mapping.get(key, [])
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            raise self.error(f'{key} must be a list of paths')
        return tuple(value)

    def reject_unknown(self, item, allowed, what):
        """Raise when a mapping contains a key outside the allowed set."""
        unknown = sorted(set(item) - set(allowed))
        if unknown:
            raise self.error(f'{what} has unknown key(s): {", ".join(unknown)}')

    def reject_keys(self, item, forbidden, what):
        """Raise when a mapping contains any of the forbidden keys."""
        present = sorted(key for key in forbidden if key in item)
        if present:
            raise self.error(f'{what} does not allow: {", ".join(present)}')

    def reject_duplicates(self, names, what):
        """Raise when a name appears more than once."""
        duplicates = sorted({name for name in names if names.count(name) > 1})
        if duplicates:
            raise self.error(f'{what}s must be unique: {", ".join(duplicates)}')
