"""Regenerate the dependency section of a chart's example page from its Chart.yaml and Chart.lock."""

import logging
from pathlib import Path

import yaml

# AI generated code: GitHub Copilot Claude Haiku 5.5
LOGGER = logging.getLogger(__name__)
START_MARKER = '<!-- chart-deps:start -->'
END_MARKER = '<!-- chart-deps:end -->'
MANUAL_MARKER = '<!-- chart-deps:manual -->'
INSERT_BEFORE = '## Minimaal'
ARTIFACTHUB_SEARCH = 'https://artifacthub.io/packages/search?ts_query_web={name}'
NO_DEPENDENCIES = 'Geen upstream dependencies.'
UNKNOWN = '-'


class ExampleDocs:
    """Rewrite the marked dependency section of one chart's example page for the chart's current version."""

    def __init__(self, root, docs_dir, source_url):
        """Store the repository root, the example page folder relative to it, and the URL of the chart sources.

        Args:
            root: Repository root that contains the charts directory.
            docs_dir: Folder with one example page per chart, named <chart>.md, relative to root.
            source_url: Base URL of the repository's sources, used to link each chart.
        """
        self.root = Path(root).resolve()
        self.docs_dir = docs_dir
        self.source_url = source_url.rstrip('/')

    def chart_directories(self):
        """Return every chart directory that contains a Chart.yaml, sorted by name."""
        return sorted(path for path in (self.root / 'charts').iterdir() if (path / 'Chart.yaml').is_file())

    def metadata(self, directory):
        """Return the parsed Chart.yaml of a chart directory."""
        return yaml.safe_load((directory / 'Chart.yaml').read_text(encoding='utf-8')) or {}

    def lock_file(self, directory):
        """Return the parsed Chart.lock of a chart directory, or None when it has no lock file."""
        lock = directory / 'Chart.lock'
        if not lock.is_file():
            return None
        return yaml.safe_load(lock.read_text(encoding='utf-8')) or {}

    def dependents(self, name):
        """Return the names of the charts that declare the chart with the given name as a dependency."""
        return [
            directory.name
            for directory in self.chart_directories()
            if any(dependency.get('name') == name for dependency in self.metadata(directory).get('dependencies') or [])
        ]

    def locked_version(self, lock, name):
        """Return the version pinned in Chart.lock for a dependency, or a dash when it is not locked."""
        if lock is None:
            return UNKNOWN
        for entry in lock.get('dependencies') or []:
            if entry.get('name') == name:
                return str(entry.get('version', UNKNOWN))
        return UNKNOWN

    def status(self, declared, locked, lock):
        """Return how the locked version compares to the version declared in Chart.yaml."""
        if lock is None:
            return 'geen lock'
        if locked == UNKNOWN:
            return 'niet in lock'
        return 'gelijk' if locked == str(declared) else 'afwijkend'

    def joined(self, values):
        """Return a list of tags or import-values as one cell, or a dash when there are none."""
        if not values:
            return UNKNOWN
        items = [f"{value['child']} -> {value['parent']}" if isinstance(value, dict) else str(value) for value in values]
        return ', '.join(items)

    def diagram(self, metadata):
        """Return the Mermaid graph of a chart and its dependencies, or a note when it has none."""
        dependencies = metadata.get('dependencies') or []
        if not dependencies:
            return NO_DEPENDENCIES
        lines = ['```mermaid', 'graph LR', f'    chart["{metadata["name"]} {metadata["version"]}"]']
        for index, dependency in enumerate(dependencies):
            lines.append(f'    dep{index}["{dependency["name"]} {dependency["version"]}"]')
            lines.append(f'    chart --> dep{index}')
        lines.append('```')
        return '\n'.join(lines)

    def table(self, dependencies, lock):
        """Return a Markdown table with the declared and locked version of each dependency."""
        lines = [
            '| Dependency | Alias | Versie (Chart.yaml) | Versie (Chart.lock) | Status | Condition | Tags | Import-values | Helm-repository | Documentatie |',
            '| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |',
        ]
        for dependency in dependencies:
            name = dependency['name']
            locked = self.locked_version(lock, name)
            cells = [
                name,
                dependency.get('alias', UNKNOWN),
                dependency['version'],
                locked,
                self.status(dependency['version'], locked, lock),
                dependency.get('condition', UNKNOWN),
                self.joined(dependency.get('tags')),
                self.joined(dependency.get('import-values')),
                dependency.get('repository', 'lokaal'),
                f'[ArtifactHub]({ARTIFACTHUB_SEARCH.format(name=name)})',
            ]
            lines.append('| ' + ' | '.join(str(cell) for cell in cells) + ' |')
        return '\n'.join(lines)

    def block(self, directory):
        """Return the marked section that is written into a chart's example page."""
        metadata = self.metadata(directory)
        lock = self.lock_file(directory)
        used_by = ', '.join(self.dependents(metadata['name'])) or 'geen andere charts.'
        parts = [
            START_MARKER,
            '### Afhankelijkheden',
            '',
            f'Bron: [charts/{directory.name}]({self.source_url}/charts/{directory.name})',
            '',
            f'Gebruikt door: {used_by}',
            '',
            self.diagram(metadata),
        ]
        if metadata.get('dependencies'):
            parts += ['', self.table(metadata['dependencies'], lock)]
            if lock is None:
                parts += ['', 'Geen Chart.lock; resolved versies zijn onbekend.']
            else:
                parts += ['', f"Chart.lock gegenereerd op {lock.get('generated', UNKNOWN)}, digest {lock.get('digest', UNKNOWN)}."]
        parts.append(END_MARKER)
        return '\n'.join(parts)

    def render_page(self, text, block):
        """Return the page text with the marked section replaced or inserted, or None when neither anchor exists."""
        if START_MARKER in text and END_MARKER in text:
            start = text.index(START_MARKER)
            end = text.index(END_MARKER) + len(END_MARKER)
            return text[:start] + block + text[end:]
        if INSERT_BEFORE not in text:
            return None
        return text.replace(INSERT_BEFORE, block + '\n\n' + INSERT_BEFORE, 1)

    def sync(self, chart, write=True):
        """Update the example page of one chart and return True when its content changes.

        Args:
            chart: Chart directory relative to the root, such as charts/spotinfo-base, or the chart name.
            write: When False, the page is not written and only the change is reported.

        Raises:
            ValueError: When the chart has no example page or the page has no place for the section.
        """
        directory = self.root / chart
        name = directory.name
        page = self.root / self.docs_dir / f'{name}.md'
        if not page.is_file():
            raise ValueError(f'{name}: example page {page} is missing')
        text = page.read_text(encoding='utf-8')
        if MANUAL_MARKER in text:
            LOGGER.info('%s: page is maintained by hand, skipping', name)
            return False
        rendered = self.render_page(text, self.block(directory))
        if rendered is None:
            raise ValueError(f'{name}: {page} has neither {START_MARKER} markers nor a {INSERT_BEFORE} section')
        if rendered == text:
            return False
        if write:
            page.write_text(rendered, encoding='utf-8')
        LOGGER.info('%s: updated %s', name, page)
        return True
