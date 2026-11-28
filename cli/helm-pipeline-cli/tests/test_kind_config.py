import contextlib
import io
import os
import tempfile
import unittest
from pathlib import Path

from helm_pipeline.charts.kind import KindTester
from helm_pipeline.charts.kind_config import KindSettingsReader
from helm_pipeline.charts.pipeline import ChartPipeline
from helm_pipeline.cli.chart_cli import ChartCli
from helm_pipeline.core.commands import CommandRunner
from case import test_case


class KindConfigTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.chart = self.root / 'charts' / 'demo'
        self.chart.mkdir(parents=True)
        self.output = self.root / 'github_output.txt'
        self.previous = os.environ.get('GITHUB_OUTPUT')
        os.environ['GITHUB_OUTPUT'] = str(self.output)

    def tearDown(self):
        if self.previous is None:
            os.environ.pop('GITHUB_OUTPUT', None)
        else:
            os.environ['GITHUB_OUTPUT'] = self.previous
        self.directory.cleanup()

    def write_config(self, text):
        (self.chart / '.ciconfig').write_text(text, encoding='utf-8')

    def outputs(self):
        return self.output.read_text(encoding='utf-8')

    def settings(self, config):
        return KindSettingsReader('charts/demo/.ciconfig').read(config, ['charts/demo/values.yaml'])

    @test_case('TC-KND-001', 'Named kind-test scenarios become the matrix list of the workflow')
    def test_named_scenarios_are_emitted_as_matrix_output(self):
        """Test that named kind-test scenarios become the matrix list of the workflow."""
        self.write_config('kind-test:\n  - name: minimal\n  - name: full\n    values-files:\n      - charts/demo/full.yaml\n')
        ChartPipeline(self.root).write_chart_config('charts/demo')
        self.assertIn('kind-scenarios=["minimal", "full"]\n', self.outputs())
        self.assertIn('kind-test=true\n', self.outputs())

    @test_case('TC-KND-002', 'A scenario without its own values-files falls back to the chart values-files')
    def test_scenario_without_values_uses_chart_values_files(self):
        """Test that a scenario without its own values-files falls back to the chart values-files."""
        config = {'values-files': ['charts/demo/ci.yaml'], 'kind-test': [{'name': 'minimal'}]}
        settings = KindSettingsReader('charts/demo/.ciconfig').read(config, config['values-files'])
        self.assertEqual(('charts/demo/ci.yaml',), settings.scenario('minimal').values_files)

    @test_case('TC-KND-003', 'A disabled kind-test still emits a non-empty matrix so GitHub accepts the workflow')
    def test_disabled_kind_test_emits_placeholder_scenario(self):
        """Test that a disabled kind-test still emits a non-empty matrix so GitHub accepts the workflow."""
        self.write_config('kind-test: false\n')
        ChartPipeline(self.root).write_chart_config('charts/demo')
        self.assertIn('kind-scenarios=["disabled"]\n', self.outputs())

    @test_case('TC-KND-004', 'Two scenarios with the same name fail, since each name maps to one cluster')
    def test_duplicate_scenario_names_are_rejected(self):
        """Test that two scenarios with the same name fail, since each name maps to one cluster."""
        with self.assertRaises(ValueError):
            self.settings({'kind-test': [{'name': 'a'}, {'name': 'a'}]})

    @test_case('TC-KND-005', 'Scenario names must be lowercase DNS-style labels')
    def test_invalid_scenario_name_is_rejected(self):
        """Test that scenario names must be lowercase DNS-style labels."""
        with self.assertRaises(ValueError):
            self.settings({'kind-test': [{'name': 'Bad Name'}]})

    @test_case('TC-KND-006', 'A prerequisite declares either a chart or manifests, not both or neither')
    def test_prerequisite_needs_exactly_one_source(self):
        """Test that a prerequisite declares either a chart or manifests, not both or neither."""
        with self.assertRaises(ValueError):
            self.settings({'kind-prerequisites': [{'name': 'cert'}]})

    @test_case('TC-KND-007', 'Kind-timeout must be a positive number of minutes')
    def test_kind_timeout_must_be_positive(self):
        """Test that kind-timeout must be a positive number of minutes."""
        with self.assertRaises(ValueError):
            self.settings({'kind-timeout': 0})

    @test_case('TC-KND-008', 'The kind plan creates the cluster, installs prerequisites, then the chart, then runs helm tests')
    def test_kind_scenario_plan_installs_prerequisites_before_chart(self):
        """Test that the kind plan creates the cluster, installs prerequisites, then the chart, then runs helm tests."""
        config = {
            'kind-test': [{'name': 'minimal'}],
            'kind-prerequisites': [
                {'name': 'cert-manager', 'namespace': 'cert-manager', 'chart': 'jetstack/cert-manager',
                 'repo': 'https://charts.jetstack.io', 'version': '1.20.0'},
                {'name': 'crds', 'manifests': 'charts/demo/ci/crds.yaml'},
            ],
        }
        settings = self.settings(config)
        scenario = settings.scenario('minimal')
        plan = KindTester(None).plan('charts/demo', scenario, settings, '1.36.4', True)
        self.assertEqual(['kind', 'create', 'cluster'], plan[0][:3])
        self.assertIn('kindest/node:v1.36.4', plan[0])
        self.assertEqual(['helm', 'dependency', 'build', 'charts/demo'], plan[1])
        self.assertEqual(
            ['helm', 'upgrade', '--install', 'cert-manager', 'jetstack/cert-manager', '--namespace', 'cert-manager',
             '--create-namespace', '--repo', 'https://charts.jetstack.io', '--version', '1.20.0', '--wait', '--timeout',
             '5m'],
            plan[2],
        )
        self.assertEqual(['kubectl', 'apply', '-f', 'charts/demo/ci/crds.yaml'], plan[3])
        self.assertEqual(['helm', 'install', 'ci-release', 'charts/demo'], plan[4][:4])
        self.assertEqual(['helm', 'test', 'ci-release', '--namespace', 'ci-test', '--logs'], plan[5])

    @test_case('TC-KND-009', 'The kind plan does not run helm test when the chart has no test hook')
    def test_helm_test_is_skipped_without_test_hooks(self):
        """Test that the kind plan does not run helm test when the chart has no test hook."""
        settings = self.settings({'kind-test': True})
        plan = KindTester(None).plan('charts/demo', settings.scenario('default'), settings, '1.36.4', False)
        self.assertNotIn('test', [command[1] for command in plan])

    @test_case('TC-KND-010', 'A helm test hook in the chart templates is detected and a chart without one is not')
    def test_chart_with_test_hook_is_detected(self):
        """Test that a helm test hook in the chart templates is detected and a chart without one is not."""
        tester = KindTester(CommandRunner(self.root))
        self.assertFalse(tester.has_test_hooks('charts/demo'))
        (self.chart / 'templates').mkdir()
        (self.chart / 'templates' / 'test-connection.yaml').write_text(
            'metadata:\n  annotations:\n    "helm.sh/hook": test\n', encoding='utf-8')
        self.assertTrue(tester.has_test_hooks('charts/demo'))

    @test_case('TC-KND-011', 'The dry-run plan creates and deletes the cluster under the name given on the command line')
    def test_kind_plan_uses_the_requested_cluster_name(self):
        """Test that the dry-run plan creates and deletes the cluster under the name given on the command line."""
        self.write_config('kind-test:\n  - name: minimal\n')
        plan = ChartPipeline(self.root).kind_plan('charts/demo', 'minimal', '1.36.4', 'local-dev')
        self.assertEqual(['kind', 'create', 'cluster', '--name', 'local-dev', '--image', 'kindest/node:v1.36.4',
                          '--wait', '180s'], plan[0])
        self.assertEqual(['helm', 'install', 'ci-release', 'charts/demo', '--namespace', 'ci-test', '--create-namespace',
                          '--wait', '--timeout', '5m'], plan[-1])

    @test_case('TC-KND-012', 'Kind-test --dry-run prints each planned command and does not touch the cluster')
    def test_dry_run_prints_plan_without_running_commands(self):
        """Test that kind-test --dry-run prints each planned command and does not touch the cluster."""
        self.write_config('kind-test:\n  - name: minimal\n')
        cli = ChartCli()
        args = cli.build_parser().parse_args(['kind-test', 'charts/demo', '--scenario', 'minimal',
                                              '--kube-version', '1.36.4', '--dry-run'])
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            cli.dispatch(args, ChartPipeline(self.root))
        lines = output.getvalue().splitlines()
        self.assertTrue(lines[0].startswith('kind create cluster --name ci'))
        self.assertIn('helm install ci-release charts/demo', lines[-1])
        self.assertNotIn('kind delete', output.getvalue())

    @test_case('TC-KND-013', '--keep-cluster and --cluster-name are available on kind-test for local debugging')
    def test_keep_cluster_flag_is_parsed(self):
        """Test that --keep-cluster and --cluster-name are available on kind-test for local debugging."""
        args = ChartCli().build_parser().parse_args(['kind-test', 'charts/demo', '--scenario', 'minimal',
                                                     '--kube-version', '1.36.4', '--keep-cluster',
                                                     '--cluster-name', 'local-dev'])
        self.assertTrue(args.keep_cluster)
        self.assertEqual('local-dev', args.cluster_name)


if __name__ == '__main__':
    unittest.main()
