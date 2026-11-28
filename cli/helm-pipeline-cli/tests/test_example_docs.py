import tempfile
import unittest
from pathlib import Path

from helm_pipeline.charts.example_docs import END_MARKER, INSERT_BEFORE, MANUAL_MARKER, START_MARKER, ExampleDocs
from case import test_case


SOURCE_URL = 'https://github.com/example/charts/tree/main'
APP_CHART = (
    'apiVersion: v2\nname: app\nversion: {version}\n'
    'dependencies:\n'
    '- name: base\n'
    '  version: 1.0.0\n'
    '  repository: file://../base\n'
)
BASE_CHART = 'apiVersion: v2\nname: base\nversion: 1.0.0\n'
APP_LOCK = 'dependencies:\n- name: base\n  repository: file://../base\n  version: 1.0.0\ngenerated: "2026-01-01T00:00:00Z"\ndigest: sha256:abc\n'
PAGE = '# app\n\nIntro.\n\n## Minimaal\n\n```yaml\nx: 1\n```\n'


class ExampleDocsTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.app = self.root / 'charts' / 'app'
        self.base = self.root / 'charts' / 'base'
        self.app.mkdir(parents=True)
        self.base.mkdir(parents=True)
        (self.base / 'Chart.yaml').write_text(BASE_CHART, encoding='utf-8')
        self.write_app('0.1.0')
        self.docs = self.root / 'docs' / 'voorbeelden'
        self.docs.mkdir(parents=True)
        self.page = self.docs / 'app.md'
        self.page.write_text(PAGE, encoding='utf-8')
        self.example_docs = ExampleDocs(self.root, 'docs/voorbeelden', SOURCE_URL)

    def tearDown(self):
        self.directory.cleanup()

    def write_app(self, version):
        (self.app / 'Chart.yaml').write_text(APP_CHART.format(version=version), encoding='utf-8')

    @test_case('TC-DOC-001', "A chart's example page gets a dependency section with its graph before the minimal example")
    def test_inserts_dependency_section_before_the_minimal_example(self):
        """Test that a chart's example page gets a dependency section with its graph before the minimal example."""
        self.assertTrue(self.example_docs.sync('charts/app'))
        text = self.page.read_text(encoding='utf-8')
        self.assertIn(START_MARKER, text)
        self.assertIn('chart["app 0.1.0"]', text)
        self.assertIn('dep0["base 1.0.0"]', text)
        self.assertLess(text.index(START_MARKER), text.index(INSERT_BEFORE))

    @test_case('TC-DOC-002', 'Regenerating a page that is already current reports no change and keeps the file as it is')
    def test_second_run_without_changes_leaves_the_page_untouched(self):
        """Test that regenerating a page that is already current reports no change and keeps the file as it is."""
        self.example_docs.sync('charts/app')
        current = self.page.read_text(encoding='utf-8')
        self.assertFalse(self.example_docs.sync('charts/app'))
        self.assertEqual(self.page.read_text(encoding='utf-8'), current)

    @test_case('TC-DOC-003', 'A new chart version replaces the old section, so the page matches the released version')
    def test_released_version_replaces_the_previous_section(self):
        """Test that a new chart version replaces the old section, so the page matches the released version."""
        self.example_docs.sync('charts/app')
        self.write_app('0.2.0')
        self.assertTrue(self.example_docs.sync('charts/app'))
        text = self.page.read_text(encoding='utf-8')
        self.assertIn('chart["app 0.2.0"]', text)
        self.assertNotIn('chart["app 0.1.0"]', text)
        self.assertEqual(text.count(START_MARKER), 1)

    @test_case('TC-DOC-004', 'The dependency table shows the version pinned in Chart.lock next to the declared one')
    def test_lock_file_shows_the_resolved_dependency_version(self):
        """Test that the dependency table shows the version pinned in Chart.lock next to the declared one."""
        (self.app / 'Chart.lock').write_text(APP_LOCK, encoding='utf-8')
        self.example_docs.sync('charts/app')
        text = self.page.read_text(encoding='utf-8')
        self.assertIn('| base | - | 1.0.0 | 1.0.0 | gelijk |', text)
        self.assertIn('Chart.lock gegenereerd op 2026-01-01T00:00:00Z, digest sha256:abc.', text)

    @test_case('TC-DOC-005', 'A chart without dependencies says so instead of showing an empty graph')
    def test_chart_without_dependencies_states_that_it_has_none(self):
        """Test that a chart without dependencies says so instead of showing an empty graph."""
        base_page = self.docs / 'base.md'
        base_page.write_text(PAGE, encoding='utf-8')
        self.example_docs.sync('charts/base')
        self.assertIn('Geen upstream dependencies.', base_page.read_text(encoding='utf-8'))

    @test_case('TC-DOC-006', "The base chart's section lists the charts that depend on it")
    def test_dependents_are_listed_as_users_of_the_chart(self):
        """Test that the base chart's section lists the charts that depend on it."""
        base_page = self.docs / 'base.md'
        base_page.write_text(PAGE, encoding='utf-8')
        self.example_docs.sync('charts/base')
        self.assertIn('Gebruikt door: app', base_page.read_text(encoding='utf-8'))

    @test_case('TC-DOC-007', 'A chart without an example page raises instead of being skipped silently')
    def test_missing_example_page_fails_loudly(self):
        """Test that a chart without an example page raises instead of being skipped silently."""
        self.page.unlink()
        with self.assertRaisesRegex(ValueError, 'example page .* is missing'):
            self.example_docs.sync('charts/app')

    @test_case('TC-DOC-008', 'A page with neither section markers nor a minimal example heading raises')
    def test_page_without_insertion_point_fails_loudly(self):
        """Test that a page with neither section markers nor a minimal example heading raises."""
        self.page.write_text('# app\n\nNo anchor here.\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'neither'):
            self.example_docs.sync('charts/app')

    @test_case('TC-DOC-009', 'Check mode reports an out-of-date page and leaves the file unchanged')
    def test_check_mode_reports_change_without_writing(self):
        """Test that check mode reports an out-of-date page and leaves the file unchanged."""
        self.assertTrue(self.example_docs.sync('charts/app', write=False))
        self.assertEqual(self.page.read_text(encoding='utf-8'), PAGE)
        self.assertNotIn(END_MARKER, self.page.read_text(encoding='utf-8'))

    @test_case('TC-DOC-010', 'Custom prose around the generated section is kept when the chart version changes')
    def test_hand_written_text_outside_the_markers_survives_regeneration(self):
        """Test that custom prose around the generated section is kept when the chart version changes."""
        self.example_docs.sync('charts/app')
        text = self.page.read_text(encoding='utf-8')
        self.page.write_text('Eigen intro.\n\n' + text + '\n## Eigen slot\n\nZelf geschreven.\n', encoding='utf-8')
        self.write_app('0.2.0')
        self.example_docs.sync('charts/app')
        updated = self.page.read_text(encoding='utf-8')
        self.assertTrue(updated.startswith('Eigen intro.'))
        self.assertIn('## Eigen slot\n\nZelf geschreven.', updated)
        self.assertIn('chart["app 0.2.0"]', updated)

    @test_case('TC-DOC-011', 'A page carrying the manual marker is left exactly as written, even when the chart changed')
    def test_page_marked_as_manual_is_never_rewritten(self):
        """Test that a page carrying the manual marker is left exactly as written, even when the chart changed."""
        manual = f'{MANUAL_MARKER}\n# app\n\nHandmatig onderhouden.\n'
        self.page.write_text(manual, encoding='utf-8')
        self.assertFalse(self.example_docs.sync('charts/app'))
        self.assertEqual(self.page.read_text(encoding='utf-8'), manual)

    @test_case('TC-DOC-012', 'Pages under a custom subfolder are never read or rewritten by the generator')
    def test_custom_pages_in_a_subfolder_are_not_touched(self):
        """Test that pages under a custom subfolder are never read or rewritten by the generator."""
        custom = self.docs / 'custom'
        custom.mkdir()
        guide = custom / 'app.md'
        guide.write_text(PAGE, encoding='utf-8')
        self.example_docs.sync('charts/app')
        self.assertEqual(guide.read_text(encoding='utf-8'), PAGE)


if __name__ == '__main__':
    unittest.main()
