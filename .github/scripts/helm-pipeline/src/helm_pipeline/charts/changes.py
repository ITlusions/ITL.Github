"""Determine which charts a change affects and write the CI matrix outputs."""

import json
import logging

LOGGER = logging.getLogger(__name__)
# Requirement files whose installed packages the dependency audit checks.
DEPENDENCY_INPUTS = ('requirements-ci.txt', 'requirements-docs.txt', 'requirements-security.txt')
# Paths that the docs and example validation job depends on.
DOCS_INPUTS = (
    'charts/', 'docs/', 'overrides/', 'scripts/', 'test/', 'plugins/helm-tests/',
    'mkdocs.yml', 'requirements-docs.txt', 'requirements-ci.txt', '.github/workflows/ci.yml',
)


def compact_json(value):
    """Serialize a value as compact JSON for GitHub Actions outputs."""
    return json.dumps(value, separators=(',', ':'))


class ChangeDetector:
    """Compare the working tree against a git base and derive the charts to build, scan, and validate."""

    def __init__(self, commands, catalog, github, versioner):
        """Store the collaborators used for git diffs, chart discovery, outputs, and tag parsing.

        Args:
            commands: A CommandRunner instance.
            catalog: A ChartCatalog instance.
            github: A GitHubFiles instance.
            versioner: A ReleaseVersioner instance, used to read the chart name from a release tag.
        """
        self.commands = commands
        self.catalog = catalog
        self.github = github
        self.versioner = versioner

    def diff_paths(self, base, develop=None, pathspec=None):
        """Return the union of paths changed from base to HEAD and, when given, from base to develop."""
        targets = ['HEAD', develop] if develop else ['HEAD']
        paths = set()
        for target in targets:
            command = ['git', 'diff', '--name-only', base, target]
            if pathspec:
                command += ['--', pathspec]
            paths.update(self.commands.run(command, capture=True).stdout.splitlines())
        return paths

    def changed(self, base, develop=None):
        """Return the effective base revision and the sorted, non-ignored charts that changed against it."""
        if not base or base == '0' * 40:
            base = 'origin/main'
        changed_charts = set()
        for path in self.diff_paths(base, develop, 'charts/'):
            parts = path.split('/')
            is_chart_file = len(parts) >= 3 and parts[0] == 'charts'
            if is_chart_file and (self.catalog.root / 'charts' / parts[1] / 'Chart.yaml').is_file():
                changed_charts.add(f'charts/{parts[1]}')
        self.catalog.log_ignored(sorted(changed_charts))
        selected = sorted(name for name in changed_charts if not self.catalog.ignored(name))
        LOGGER.info('Found %d changed chart(s) against %s: %s', len(selected), base, ', '.join(selected) or 'none')
        return base, selected

    def changed_paths(self, base, develop=None):
        """Return every repository path that differs between the base revision and HEAD or develop."""
        return sorted(self.diff_paths(base, develop))

    @staticmethod
    def touches(paths, prefixes):
        """Return True when any changed path equals or lies under one of the given prefixes."""
        return any(path.startswith(prefix) for path in paths for prefix in prefixes)

    def affected_charts(self, changed):
        """Return the changed charts plus every chart that depends on them, transitively."""
        charts = {}
        for metadata_path in (self.catalog.root / 'charts').glob('*/Chart.yaml'):
            chart = metadata_path.parent
            metadata = self.catalog.metadata(chart)
            charts[f'charts/{chart.name}'] = (metadata.get('name', chart.name), metadata.get('dependencies') or [])
        affected = set(changed)
        while True:
            names = {charts[chart][0] for chart in affected if chart in charts}
            dependents = {
                path for path, (_, dependencies) in charts.items()
                if any(dependency.get('name') in names for dependency in dependencies)
            }
            expanded = affected | dependents
            if expanded == affected:
                return sorted(affected)
            affected = expanded

    def write_changed(self, base, scan_all=False, selected_chart=None, tag=None, develop=None):
        """Write the charts, affected, base, docs, dependencies, and validate outputs for the workflow matrix."""
        if tag:
            selected_chart = self.versioner.chart_from_tag(tag)
        if selected_chart:
            base, charts = 'HEAD', []
            docs = dependencies = True
            affected = [self.catalog.validated_chart(selected_chart)]
            validate = affected
        else:
            # Full scans keep the diff base so render-diff and security scans still compare against the target branch.
            base, charts = self.changed(base, develop)
            paths = self.changed_paths(base, develop)
            docs = self.touches(paths, DOCS_INPUTS)
            dependencies = self.touches(paths, DEPENDENCY_INPUTS)
            if scan_all:
                docs = dependencies = True
                affected = self.catalog.all_charts()
            else:
                expanded = self.affected_charts(charts)
                self.catalog.log_ignored(sorted(set(expanded) - set(charts)))
                affected = [chart for chart in expanded if not self.catalog.ignored(chart)]
            validate = self.catalog.all_charts()
        LOGGER.info('Affected charts: %s', ', '.join(affected) or 'none')
        outputs = {
            'charts': compact_json(charts),
            'affected': compact_json(affected),
            'base': base,
            'docs': str(docs).lower(),
            'dependencies': str(dependencies).lower(),
            'validate': compact_json(validate),
        }
        self.github.emit('GITHUB_OUTPUT', ''.join(f'{key}={value}\n' for key, value in outputs.items()))
