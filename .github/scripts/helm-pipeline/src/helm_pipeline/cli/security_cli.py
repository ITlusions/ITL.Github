"""Command-line entry point for the security scans. Holds argument parsing only and delegates each step to SecurityPipeline."""

import argparse
import json
import logging
import os
import subprocess
import sys
from pathlib import Path

from helm_pipeline.core.logging_config import configure_logging
from helm_pipeline.security.kubescape_report import KubescapeReport
from helm_pipeline.security.pipeline import SecurityPipeline
from helm_pipeline.security.pipeline_cost import PipelineCost
from helm_pipeline.security.summary import KUBESCAPE_REPORT, SecuritySummary
from helm_pipeline.security.summary_layouts import DEFAULT_LAYOUT
from helm_pipeline.security.tools import SecurityToolInstaller

# AI generated code: GitHub Copilot Claude Haiku 5.5
LOGGER = logging.getLogger(__name__)


class SecurityCli:
    """Parse the security-scan arguments and run the requested step on a SecurityPipeline."""

    def build_parser(self):
        """Return the argument parser with one subcommand per security step."""
        parser = argparse.ArgumentParser(description='SpotINFO security scans')
        commands = parser.add_subparsers(dest='command', required=True)
        setup = commands.add_parser('setup-tools')
        setup.add_argument('--directory', required=True)
        setup.add_argument('--tool', action='append', required=True, choices=SecurityToolInstaller.TOOLS)
        commands.add_parser('repository')
        secrets = commands.add_parser('secrets')
        secrets.add_argument('--base', default='', help='scan only commits after this revision')
        commands.add_parser('dependencies')
        chart = commands.add_parser('chart')
        chart.add_argument('chart', nargs='?', default=os.environ.get('CHART'))
        pipeline_cost = commands.add_parser('pipeline-cost')
        pipeline_cost.add_argument('--jobs', required=True, help='JSON file from gh run view --json jobs')
        return parser

    def run(self, argv=None):
        """Parse the arguments and run the requested security step.

        Args:
            argv: Argument list, or None to read sys.argv.
        """
        parser = self.build_parser()
        args = parser.parse_args(argv)
        configure_logging()
        if args.command == 'chart' and not args.chart:
            parser.error('chart or CHART is required')
        pipeline = SecurityPipeline(Path.cwd())
        summary = SecuritySummary(pipeline.github, pipeline.root,
                                  os.environ.get('SECURITY_SUMMARY_LAYOUT', DEFAULT_LAYOUT))
        try:
            self.dispatch(args, pipeline)
        except subprocess.CalledProcessError as error:
            self.log_failing_controls(args, pipeline)
            LOGGER.error('Security scan stopped: %s exited with code %s. Review the findings above.',
                         ' '.join(str(part) for part in error.cmd[:2]), error.returncode)
            sys.exit(1)
        except Exception as error:
            LOGGER.error('Security scan failed: %s', error)
            LOGGER.debug('Traceback for the failure above', exc_info=True)
            sys.exit(1)
        finally:
            summary.write(args.command, getattr(args, 'chart', None))

    def log_failing_controls(self, args, pipeline):
        """Log each failed Kubescape control of a chart scan in plain words.

        Args:
            args: Parsed arguments; only chart scans have Kubescape controls to report.
            pipeline: SecurityPipeline whose root holds the report directory.
        """
        if args.command != 'chart':
            return
        report = pipeline.root / 'dist' / 'security' / Path(args.chart).name / KUBESCAPE_REPORT
        for control in KubescapeReport(report).failing_controls():
            LOGGER.error('Kubescape control %s (%s) failed on %s resource(s)',
                         control['id'], control['name'], control['resources'])

    def dispatch(self, args, pipeline):
        """Run the step named by the parsed arguments on the pipeline."""
        if args.command == 'setup-tools':
            pipeline.setup_tools(args.directory, args.tool)
        elif args.command == 'repository':
            pipeline.scan_repository()
        elif args.command == 'secrets':
            pipeline.scan_secrets(args.base or None)
        elif args.command == 'dependencies':
            pipeline.audit_dependencies()
        elif args.command == 'pipeline-cost':
            PipelineCost(pipeline.github).write(json.loads(Path(args.jobs).read_text(encoding='utf-8'))['jobs'])
        elif args.command == 'chart':
            pipeline.scan_chart(args.chart)


def main():
    """Entry point for the security-scan console script."""
    SecurityCli().run()


if __name__ == '__main__':
    main()
