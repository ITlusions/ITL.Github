"""Command-line entry point for the Helm chart CI. Holds argument parsing only and delegates each step to ChartPipeline."""

import argparse
import json
import os
import shlex
from pathlib import Path

from helm_pipeline.charts.example_docs import ExampleDocs
from helm_pipeline.charts.kind import CLUSTER_NAME
from helm_pipeline.charts.pipeline import ChartPipeline
from helm_pipeline.core.logging_config import configure_logging
from helm_pipeline.testing.chart_requirements import run_chart_requirements


CHART_REQUIRED_COMMANDS = ('validate', 'check-version', 'next-version', 'render-diff', 'publish', 'package', 'kind-test', 'docs-examples', 'test-requirements')


class ChartCli:
    """Parse the chart CI arguments and run the requested step on a ChartPipeline."""

    def build_parser(self):
        """Return the argument parser with one subcommand per CI step."""
        parser = argparse.ArgumentParser(description='SpotINFO Helm chart CI')
        commands = parser.add_subparsers(dest='command', required=True)
        changed = commands.add_parser('changed')
        changed.add_argument('--base', default=os.environ.get('BASE_SHA', ''))
        changed.add_argument('--all', action='store_true', default=os.environ.get('SCAN_ALL') == '1')
        changed.add_argument('--chart', default=os.environ.get('SCAN_CHART'))
        changed.add_argument('--tag', default=os.environ.get('RELEASE_TAG') or None)
        changed.add_argument('--develop', default=None)
        commands.add_parser('chart-config').add_argument('chart', nargs='?', default=os.environ.get('CHART_PATH', '.'))
        commands.add_parser('security-charts').add_argument('--affected', default=os.environ.get('AFFECTED', '[]'))
        commands.add_parser('setup-tools').add_argument('--directory', required=True)
        commands.add_parser('setup-kind').add_argument('--directory', required=True)
        commands.add_parser('lint-all')
        commands.add_parser('check-requirements')
        commands.add_parser('check-locks').add_argument('chart', nargs='?')
        for name in ('validate', 'check-version', 'next-version', 'publish'):
            commands.add_parser(name).add_argument('chart', nargs='?', default=os.environ.get('CHART'))
        kind = commands.add_parser('kind-test')
        kind.add_argument('chart', nargs='?', default=os.environ.get('CHART'))
        kind.add_argument('--scenario', default=os.environ.get('SCENARIO'))
        kind.add_argument('--kube-version', default=os.environ.get('KUBE_VERSION'))
        kind.add_argument('--cluster-name', default=os.environ.get('CLUSTER_NAME', CLUSTER_NAME))
        kind.add_argument('--keep-cluster', action='store_true')
        kind.add_argument('--dry-run', action='store_true')
        diff = commands.add_parser('render-diff')
        diff.add_argument('chart', nargs='?', default=os.environ.get('CHART'))
        diff.add_argument('base', nargs='?', default=os.environ.get('BASE_SHA'))
        package = commands.add_parser('package')
        package.add_argument('chart', nargs='?', default=os.environ.get('CHART'))
        package.add_argument('--destination', default='dist/packages')
        docs = commands.add_parser('docs-examples')
        docs.add_argument('chart', nargs='?', default=os.environ.get('CHART'))
        docs.add_argument('--docs-dir', default='docs/voorbeelden')
        docs.add_argument('--check', action='store_true', help='exit 1 instead of writing when the page is out of date')
        requirements = commands.add_parser('test-requirements')
        requirements.add_argument('chart', nargs='?', default=os.environ.get('CHART'))
        return parser

    def run(self, argv=None):
        """Parse the arguments, validate the chart and base inputs, and run the requested step.

        Args:
            argv: Argument list, or None to read sys.argv.
        """
        parser = self.build_parser()
        args = parser.parse_args(argv)
        configure_logging()
        if args.command in CHART_REQUIRED_COMMANDS and not args.chart:
            parser.error('chart or CHART is required')
        if args.command == 'render-diff' and not args.base:
            parser.error('base or BASE_SHA is required')
        if args.command == 'kind-test' and not (args.scenario and args.kube_version):
            parser.error('scenario or SCENARIO and kube-version or KUBE_VERSION are required')
        self.dispatch(args, ChartPipeline(Path.cwd()))

    def dispatch(self, args, ci):
        """Run the step named by the parsed arguments on the pipeline."""
        if args.command == 'changed':
            ci.write_changed(args.base, scan_all=args.all, selected_chart=args.chart, tag=args.tag, develop=args.develop)
        elif args.command == 'chart-config':
            ci.write_chart_config(args.chart)
        elif args.command == 'security-charts':
            ci.write_security_charts(json.loads(args.affected))
        elif args.command == 'setup-tools':
            ci.setup_tools(args.directory)
        elif args.command == 'setup-kind':
            ci.setup_kind(args.directory)
        elif args.command == 'lint-all':
            ci.lint_all()
        elif args.command == 'check-requirements':
            ci.check_requirements()
        elif args.command == 'check-locks':
            ci.check_locks(args.chart)
        elif args.command == 'validate':
            ci.add_repositories()
            ci.validate(args.chart)
        elif args.command == 'check-version':
            ci.check_version(args.chart)
        elif args.command == 'next-version':
            ci.next_version(args.chart, os.environ.get('GITHUB_REF', ''), os.environ.get('GITHUB_RUN_NUMBER', '0'),
                            os.environ.get('GITHUB_SHA', ''))
        elif args.command == 'render-diff':
            ci.add_repositories()
            ci.render_diff(args.chart, args.base)
        elif args.command == 'package':
            ci.add_repositories()
            ci.package(args.chart, args.destination)
        elif args.command == 'kind-test' and args.dry_run:
            for command in ci.kind_plan(args.chart, args.scenario, args.kube_version, args.cluster_name):
                print(shlex.join(command))
        elif args.command == 'kind-test':
            ci.add_repositories()
            ci.kind_test(args.chart, args.scenario, args.kube_version, args.cluster_name, args.keep_cluster)
        elif args.command == 'publish':
            ci.publish(args.chart, os.environ.get('REGISTRY_HOST'), os.environ.get('REGISTRY_USERNAME'),
                       os.environ.get('REGISTRY_PASSWORD'))
        elif args.command == 'docs-examples':
            self.update_example_docs(args)
        elif args.command == 'test-requirements':
            if not run_chart_requirements(Path.cwd(), args.chart):
                raise SystemExit(1)

    def update_example_docs(self, args):
        """Regenerate the example page of one chart; with --check, exit 1 when the page is out of date."""
        source = f"{os.environ.get('GITHUB_SERVER_URL', 'https://github.com')}/{os.environ.get('GITHUB_REPOSITORY', '')}/tree/main"
        changed = ExampleDocs(Path.cwd(), args.docs_dir, source).sync(args.chart, write=not args.check)
        if args.check and changed:
            raise SystemExit(1)


def main():
    """Entry point for the chart-pipeline console script."""
    ChartCli().run()


if __name__ == '__main__':
    main()
