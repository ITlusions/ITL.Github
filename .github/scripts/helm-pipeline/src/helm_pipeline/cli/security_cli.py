"""Command-line entry point for the security scans. Holds argument parsing only and delegates each step to SecurityPipeline."""

import argparse
import os
from pathlib import Path

from helm_pipeline.core.logging_config import configure_logging
from helm_pipeline.security.pipeline import SecurityPipeline
from helm_pipeline.security.summary import SecuritySummary
from helm_pipeline.security.tools import SecurityToolInstaller

# AI generated code: GitHub Copilot Claude Haiku 5.5


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
        summary = SecuritySummary(pipeline.github, pipeline.root)
        try:
            self.dispatch(args, pipeline)
        finally:
            summary.write(args.command, getattr(args, 'chart', None))

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
        elif args.command == 'chart':
            pipeline.scan_chart(args.chart)


def main():
    """Entry point for the security-scan console script."""
    SecurityCli().run()


if __name__ == '__main__':
    main()
