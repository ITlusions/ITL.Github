"""Command-line entry point that tags a test folder and regenerates its test registry."""

import argparse
from pathlib import Path

from helm_pipeline.testing.tagging import Tagger



def main(argv=None):
    """Parse the arguments and run the tagger on the test folder."""
    parser = argparse.ArgumentParser(description='Tag test methods with test_case IDs and regenerate REGISTRY.md')
    parser.add_argument('--tests', type=Path, default=Path('tests'), help='test folder with areas.yaml')
    parser.add_argument('--check', action='store_true', help='exit 1 instead of writing when tests or the registry are out of date')
    args = parser.parse_args(argv)
    return Tagger(args.tests).run(check=args.check)
