"""Plan and run the kind install and test of one chart scenario."""

import re

CLUSTER_NAME = 'ci'
CLUSTER_WAIT = '180s'
RELEASE_NAME = 'ci-release'
# AI generated code: GitHub Copilot Claude Haiku 5.5
TEST_HOOK_PATTERN = re.compile(r'helm\.sh/hook.*test')


class KindTester:
    """Build the command plan for a kind scenario and execute it against a throwaway cluster."""

    def __init__(self, commands):
        """Store the command runner.

        Args:
            commands: A CommandRunner instance.
        """
        self.commands = commands

    def plan(self, chart, scenario, settings, kube_version, has_test_hooks, cluster_name=CLUSTER_NAME):
        """Return the ordered commands that test one scenario of a chart.

        Args:
            chart: Chart path relative to the repository root.
            scenario: The KindScenario to install.
            settings: The chart's KindSettings.
            kube_version: Kubernetes version of the kind node image.
            has_test_hooks: Whether the chart ships helm test hooks.
            cluster_name: Name of the kind cluster to create.

        Returns:
            A list of argument lists, one per command.
        """
        commands = [
            [
                'kind', 'create', 'cluster', '--name', cluster_name,
                '--image', f'kindest/node:v{kube_version}', '--wait', CLUSTER_WAIT,
            ],
            ['helm', 'dependency', 'build', chart],
        ]
        for prerequisite in settings.prerequisites:
            commands.append(self.prerequisite_command(prerequisite, settings.timeout_minutes))
        commands.append(
            [
                'helm', 'install', RELEASE_NAME, chart,
                '--namespace', settings.namespace, '--create-namespace',
                *self.values_arguments(scenario.values_files),
                '--wait', '--timeout', f'{settings.timeout_minutes}m',
            ]
        )
        if has_test_hooks:
            commands.append(['helm', 'test', RELEASE_NAME, '--namespace', settings.namespace, '--logs'])
        return commands

    def prerequisite_command(self, prerequisite, timeout_minutes):
        """Return the command that installs one prerequisite, either a chart or a manifest set."""
        if prerequisite.manifests:
            return ['kubectl', 'apply', '-f', prerequisite.manifests]
        command = [
            'helm', 'upgrade', '--install', prerequisite.name, prerequisite.chart,
            '--namespace', prerequisite.namespace, '--create-namespace',
        ]
        if prerequisite.repo:
            command += ['--repo', prerequisite.repo]
        if prerequisite.version:
            command += ['--version', prerequisite.version]
        command += self.values_arguments(prerequisite.values_files)
        command += ['--wait', '--timeout', f'{timeout_minutes}m']
        return command

    def values_arguments(self, files):
        """Return the --values arguments for a list of values files."""
        arguments = []
        for file in files:
            arguments += ['--values', file]
        return arguments

    def has_test_hooks(self, chart):
        """Return whether any template of the chart declares a helm test hook."""
        templates = self.commands.root / chart / 'templates'
        if not templates.is_dir():
            return False
        for path in templates.rglob('*'):
            if path.is_file() and TEST_HOOK_PATTERN.search(path.read_text(encoding='utf-8')):
                return True
        return False

    def plan_for(self, chart, settings, scenario_name, kube_version, cluster_name=CLUSTER_NAME):
        """Return the ordered commands for one named scenario, detecting helm test hooks in the chart.

        Args:
            chart: Chart path relative to the repository root.
            settings: The chart's KindSettings.
            scenario_name: Name of the scenario to plan.
            kube_version: Kubernetes version of the kind node image.
            cluster_name: Name of the kind cluster to create.

        Returns:
            A list of argument lists, one per command.
        """
        scenario = settings.scenario(scenario_name)
        return self.plan(chart, scenario, settings, kube_version, self.has_test_hooks(chart), cluster_name)

    def run(self, chart, settings, scenario_name, kube_version, cluster_name=CLUSTER_NAME, keep_cluster=False):
        """Create a cluster, install the chart for one scenario, run its helm tests, and delete the cluster.

        Args:
            chart: Chart path relative to the repository root.
            settings: The chart's KindSettings.
            scenario_name: Name of the scenario to run.
            kube_version: Kubernetes version of the kind node image.
            cluster_name: Name of the kind cluster to create.
            keep_cluster: Leave the cluster running after the run, for debugging.
        """
        plan = self.plan_for(chart, settings, scenario_name, kube_version, cluster_name)
        try:
            for command in plan:
                self.commands.run(command)
        finally:
            if not keep_cluster:
                self.commands.run(['kind', 'delete', 'cluster', '--name', cluster_name], check=False)
