import os
import tempfile
import unittest
from pathlib import Path

from helm_pipeline.charts.pipeline import ChartPipeline


class ChartConfigTest(unittest.TestCase):
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

    def test_missing_ciconfig_writes_empty_outputs(self):
        """Test that a chart without .ciconfig leaves every setting empty so the workflow inputs apply."""
        ChartPipeline(self.root).write_chart_config('charts/demo')
        text = self.outputs()
        self.assertIn('timeout-minutes=\n', text)
        self.assertIn('helm-version=\n', text)
        self.assertIn('kubeconform=\n', text)
        self.assertIn('values-files=\n', text)

    def test_kind_test_is_disabled_when_unset(self):
        """Test that kind tests stay disabled for a chart whose .ciconfig does not enable them."""
        ChartPipeline(self.root).write_chart_config('charts/demo')
        self.assertIn('kind-test=\n', self.outputs())

    def test_kind_test_is_enabled_by_ciconfig(self):
        """Test that kind-test: true in .ciconfig is emitted as an enabled workflow output."""
        self.write_config('kind-test: true\n')
        ChartPipeline(self.root).write_chart_config('charts/demo')
        self.assertIn('kind-test=true\n', self.outputs())

    def test_kind_test_must_be_a_boolean(self):
        """Test that a non-boolean kind-test value fails instead of enabling tests by accident."""
        self.write_config('kind-test: yes please\n')
        with self.assertRaises(ValueError):
            ChartPipeline(self.root).write_chart_config('charts/demo')

    def test_ciconfig_settings_are_written_as_outputs(self):
        """Test that every .ciconfig setting is emitted as a GitHub Actions output."""
        self.write_config(
            'timeout-minutes: 45\n'
            'helm-version: v4.2.0\n'
            'kube-version: 1.36.4\n'
            'kubeconform: false\n'
            'values-files:\n'
            '  - charts/demo/ci/a.yaml\n'
            '  - charts/demo/ci/b.yaml\n'
        )
        ChartPipeline(self.root).write_chart_config('charts/demo')
        text = self.outputs()
        self.assertIn('timeout-minutes=45\n', text)
        self.assertIn('helm-version=v4.2.0\n', text)
        self.assertIn('kube-version=1.36.4\n', text)
        self.assertIn('kubeconform=false\n', text)
        self.assertIn('values-files<<CONFIGCI_EOF\ncharts/demo/ci/a.yaml\ncharts/demo/ci/b.yaml\nCONFIGCI_EOF\n', text)

    def test_scanners_are_enabled_by_default(self):
        """Test that trivy and kubescape both run for a chart whose .ciconfig does not set them."""
        config = ChartPipeline(self.root).config
        self.assertTrue(config.scanner_enabled('charts/demo', 'trivy'))
        self.assertTrue(config.scanner_enabled('charts/demo', 'kubescape'))

    def test_scanners_can_be_disabled_by_ciconfig(self):
        """Test that trivy: false and kubescape: false in .ciconfig turn off the respective scanner."""
        self.write_config('trivy: false\nkubescape: false\n')
        config = ChartPipeline(self.root).config
        self.assertFalse(config.scanner_enabled('charts/demo', 'trivy'))
        self.assertFalse(config.scanner_enabled('charts/demo', 'kubescape'))

    def test_scanner_switch_must_be_a_boolean(self):
        """Test that a non-boolean trivy value fails instead of silently leaving the scanner on."""
        self.write_config('trivy: "no"\n')
        with self.assertRaises(ValueError):
            ChartPipeline(self.root).chart_config('charts/demo')

    def test_security_charts_skip_charts_with_both_scanners_off(self):
        """Test that a chart with trivy and kubescape both false is left out of the security-charts output."""
        self.write_config('trivy: false\nkubescape: false\n')
        other = self.root / 'charts' / 'other'
        other.mkdir()
        ChartPipeline(self.root).write_security_charts(['charts/demo', 'charts/other'])
        self.assertIn('security-charts=["other"]\n', self.outputs())

    def test_security_charts_keep_charts_with_one_scanner_on(self):
        """Test that a chart with only one scanner disabled still gets a security job."""
        self.write_config('trivy: false\n')
        ChartPipeline(self.root).write_security_charts(['charts/demo'])
        self.assertIn('security-charts=["demo"]\n', self.outputs())

    def test_security_charts_is_empty_when_nothing_is_scanned(self):
        """Test that an empty security-charts list is written when every affected chart opted out."""
        self.write_config('trivy: false\nkubescape: false\n')
        ChartPipeline(self.root).write_security_charts(['charts/demo'])
        self.assertIn('security-charts=[]\n', self.outputs())

    def test_unknown_key_is_rejected(self):
        """Test that a misspelled .ciconfig key fails instead of being silently ignored."""
        self.write_config('timeout: 30\n')
        with self.assertRaises(ValueError):
            ChartPipeline(self.root).write_chart_config('charts/demo')

    def test_values_files_must_be_a_list(self):
        """Test that values-files must be a list of paths."""
        self.write_config('values-files: charts/demo/ci/a.yaml\n')
        with self.assertRaises(ValueError):
            ChartPipeline(self.root).chart_config('charts/demo')


if __name__ == '__main__':
    unittest.main()
