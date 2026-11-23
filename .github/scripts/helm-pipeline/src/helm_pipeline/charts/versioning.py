"""Derive release versions from chart tags and Chart.yaml, and write the version outputs."""

import logging
import re
from pathlib import Path

LOGGER = logging.getLogger(__name__)
SEMVER = re.compile(r'(\d+)\.(\d+)\.(\d+)')


class ReleaseVersioner:
    """Compute chart versions for release and non-release builds."""

    def __init__(self, commands, catalog, github):
        """Store the collaborators used for git tags, chart metadata, and outputs.

        Args:
            commands: A CommandRunner instance.
            catalog: A ChartCatalog instance.
            github: A GitHubFiles instance.
        """
        self.commands = commands
        self.catalog = catalog
        self.github = github

    def chart_from_tag(self, tag):
        """Return the chart name from a tag of the form chart/<chart-name>/v<version>."""
        match = re.fullmatch(r'chart/([a-z0-9-]+)/v\d+\.\d+\.\d+', tag)
        if not match:
            raise ValueError(f'Tag does not have the form chart/<chart-name>/v<version>: {tag}')
        return match.group(1)

    def released_version(self, chart):
        """Return the next release version: the highest chart tag bumped by one patch, never below Chart.yaml."""
        metadata = self.catalog.metadata(chart)
        name = metadata.get('name', chart.name)
        floor = tuple(int(part) for part in SEMVER.fullmatch(str(metadata.get('version', ''))).groups())
        prefix = f'chart/{name}/v'
        tags = self.commands.run(['git', 'tag', '--list', f'{prefix}*'], capture=True).stdout.split()
        released = []
        for tag in tags:
            match = SEMVER.fullmatch(tag.removeprefix(prefix))
            if match:
                released.append(tuple(int(part) for part in match.groups()))
        if not released:
            return '.'.join(map(str, floor))
        major, minor, patch = max(released)
        return '.'.join(map(str, max(floor, (major, minor, patch + 1))))

    def next_version(self, chart, ref, run_number, sha):
        """Compute the chart version for this build and write the version, is-release and tag outputs."""
        chart = Path(chart).resolve()
        release = self.released_version(chart)
        name = self.catalog.metadata(chart).get('name', chart.name)
        if ref == 'refs/heads/main':
            version, is_release, tag = release, 'true', f'chart/{name}/v{release}'
        else:
            branch = ref.removeprefix('refs/heads/')
            slug = re.sub(r'[^a-z0-9]+', '-', branch.lower()).strip('-')
            version, is_release, tag = f'{release}-{slug}.{run_number}-{sha[:7]}', 'false', ''
        self.github.emit('GITHUB_OUTPUT', f'version={version}\nis-release={is_release}\ntag={tag}\n')
        LOGGER.info('Version for %s: %s (release: %s)', name, version, is_release)
        return version
