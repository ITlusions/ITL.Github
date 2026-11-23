"""Tests for the combined per-chart exception file."""

import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

import yaml

from helm_pipeline.security.chart_exceptions import ChartExceptions

# AI generated code: GitHub Copilot Claude Haiku 5.5
EXCEPTION_FILE = """\
trivy:
  misconfigurations:
    - id: AVD-KSV-0014
      statement: Read-only root filesystem is not supported by the image.
      owner: team-platform
      expires: 2030-01-31
      request: ITlusions/spotinfo-helm-charts#42
kubescape:
  - name: allow-root-filesystem
    policyType: postureExceptionPolicy
    actions:
      - alertAndMoveOn
    resources: []
    posturePolicies:
      - controlID: C-0017
    owner: team-platform
    expires: 2030-01-31
    request: ITlusions/spotinfo-helm-charts#42
"""
TODAY = date(2026, 11, 23)


class ChartExceptionsTest(unittest.TestCase):
    """Behavioral tests for splitting the exception file into the Trivy and Kubescape inputs."""

    def write_chart_file(self, root, content):
        """Write the exception file of the demo chart below the repository root."""
        folder = root / 'security' / 'exceptions'
        folder.mkdir(parents=True, exist_ok=True)
        (folder / 'demo.yaml').write_text(content, encoding='utf-8')

    def test_chart_without_exception_file_produces_no_inputs(self):
        """Test that a chart without an exception file produces no Trivy or Kubescape exception input."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            output = root / 'out'
            output.mkdir()
            exceptions = ChartExceptions(root, None)
            self.assertIsNone(exceptions.trivy_ignorefile('demo', output))
            self.assertIsNone(exceptions.kubescape_exception_file('demo', output))
            self.assertEqual(list(output.iterdir()), [])

    def test_trivy_section_is_written_as_ignorefile_with_categories_at_top_level(self):
        """Test that the trivy section becomes a Trivy ignore file whose categories sit at the top level."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            output = root / 'out'
            output.mkdir()
            self.write_chart_file(root, EXCEPTION_FILE)
            path = Path(ChartExceptions(root, None).trivy_ignorefile('demo', output))
            written = yaml.safe_load(path.read_text(encoding='utf-8'))
        self.assertEqual(written, {'misconfigurations': [{
            'id': 'AVD-KSV-0014',
            'statement': 'Read-only root filesystem is not supported by the image.',
        }]})

    def test_kubescape_section_is_written_as_json_exception_list(self):
        """Test that the kubescape section becomes the JSON exception list Kubescape reads."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            output = root / 'out'
            output.mkdir()
            self.write_chart_file(root, EXCEPTION_FILE)
            path = Path(ChartExceptions(root, None).kubescape_exception_file('demo', output))
            written = json.loads(path.read_text(encoding='utf-8'))
        self.assertEqual(written[0]['name'], 'allow-root-filesystem')
        self.assertEqual(written[0]['posturePolicies'], [{'controlID': 'C-0017'}])

    def test_exception_file_in_chart_root_is_found_as_json(self):
        """Test that an exceptions.json in the chart root is used as the chart's exception file."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            output = root / 'out'
            output.mkdir()
            chart = root / 'charts' / 'demo'
            chart.mkdir(parents=True)
            entry = {'name': 'allow-root-filesystem', 'posturePolicies': [{'controlID': 'C-0017'}]}
            metadata = {'owner': 'team-platform', 'expires': '2030-01-31', 'request': 'ITlusions/spotinfo-helm-charts#42'}
            (chart / 'exceptions.json').write_text(json.dumps({'kubescape': [{**entry, **metadata}]}), encoding='utf-8')
            path = Path(ChartExceptions(root, None).kubescape_exception_file('demo', output))
            self.assertEqual(json.loads(path.read_text(encoding='utf-8')), [entry])

    def test_two_exception_files_for_one_chart_are_rejected(self):
        """Test that a chart with both a chart-root and a security-folder exception file fails instead of guessing."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            self.write_chart_file(root, EXCEPTION_FILE)
            chart = root / 'charts' / 'demo'
            chart.mkdir(parents=True)
            (chart / 'exceptions.yaml').write_text('{}', encoding='utf-8')
            with self.assertRaises(RuntimeError):
                ChartExceptions(root, None).path_for('demo')

    def test_trivy_statements_map_each_suppressed_id_to_its_statement(self):
        """Test that the suppressed Trivy IDs can be looked up with their statement for the job summary."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            self.write_chart_file(root, EXCEPTION_FILE)
            statements = ChartExceptions(root, None).trivy_statements('demo')
        self.assertEqual(
            statements,
            {'AVD-KSV-0014': 'Read-only root filesystem is not supported by the image.'},
        )

    def test_exclusion_without_owner_expiry_or_request_is_rejected(self):
        """Test that an exclusion missing its owner, expiry or request fails instead of being applied silently."""
        content = 'trivy:\n  misconfigurations:\n    - id: AVD-KSV-0014\n      statement: No metadata.\n'
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            self.write_chart_file(root, content)
            with self.assertRaises(RuntimeError):
                ChartExceptions(root, None, today=TODAY).exclusions('demo')

    def test_exclusion_with_invalid_expiry_date_is_rejected(self):
        """Test that an exclusion whose expiry is not an ISO date fails the scan."""
        content = (
            'trivy:\n  misconfigurations:\n    - id: AVD-KSV-0014\n      statement: Bad date.\n'
            '      owner: team-platform\n      expires: next-year\n      request: 42\n'
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            self.write_chart_file(root, content)
            with self.assertRaises(RuntimeError):
                ChartExceptions(root, None, today=TODAY).exclusions('demo')

    def test_expired_exclusion_is_left_out_of_the_ignorefile_and_reported_as_expired(self):
        """Test that an exclusion past its expiry no longer suppresses its finding and is reported as expired."""
        content = (
            'trivy:\n  misconfigurations:\n    - id: AVD-KSV-0014\n      statement: Old exclusion.\n'
            '      owner: team-platform\n      expires: 2020-01-31\n      request: 42\n'
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            output = root / 'out'
            output.mkdir()
            self.write_chart_file(root, content)
            exceptions = ChartExceptions(root, None, today=TODAY)
            ignorefile = exceptions.trivy_ignorefile('demo', output)
            rows = exceptions.exclusions('demo')
        self.assertIsNone(ignorefile)
        self.assertEqual(rows[0]['status'], 'expired')
        self.assertEqual(rows[0]['owner'], 'team-platform')
        self.assertEqual(rows[0]['request'], '42')

    def test_active_exclusion_reports_owner_expiry_and_request_for_the_summary(self):
        """Test that every exclusion row carries its owner, expiry date and request for the job summary."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            self.write_chart_file(root, EXCEPTION_FILE)
            rows = ChartExceptions(root, None, today=TODAY).exclusions('demo')
        self.assertEqual([row['scanner'] for row in rows], ['trivy', 'kubescape'])
        self.assertEqual(rows[1]['detail'], 'allow-root-filesystem')
        self.assertEqual(rows[1]['id'], 'C-0017')
        for row in rows:
            self.assertEqual(row['status'], 'active')
            self.assertEqual(row['owner'], 'team-platform')
            self.assertEqual(row['expires'], '2030-01-31')
            self.assertEqual(row['request'], 'ITlusions/spotinfo-helm-charts#42')


if __name__ == '__main__':
    unittest.main()
