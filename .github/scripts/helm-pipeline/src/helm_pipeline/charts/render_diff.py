"""Render charts at a base revision and at HEAD, and publish a Markdown diff to the job summary."""

import difflib
import logging
import tempfile
from pathlib import Path

LOGGER = logging.getLogger(__name__)


class RenderDiffer:
    """Compare the rendered minimal example of a chart between a base revision and the working tree."""

    def __init__(self, commands, catalog, helm, github):
        """Store the collaborators used for git worktrees, chart metadata, rendering, and the job summary.

        Args:
            commands: A CommandRunner instance.
            catalog: A ChartCatalog instance.
            helm: A HelmClient instance.
            github: A GitHubFiles instance.
        """
        self.commands = commands
        self.catalog = catalog
        self.helm = helm
        self.github = github

    def render_diff(self, chart, base):
        """Write a summary of how the chart's rendered output differs from the base revision."""
        chart = Path(chart).resolve()
        relative = chart.relative_to(self.catalog.root).as_posix()
        if self.commands.run(
            ['git', 'cat-file', '-e', f'{base}:{relative}/Chart.yaml'], capture=True, check=False,
        ).returncode:
            message = f'{chart.name} does not exist in {base}; no comparison\n'
        elif self.catalog.metadata(chart).get('type') == 'library':
            message = f'{chart.name} is a library chart; no render diff\n'
        else:
            LOGGER.info('Rendering %s against %s', chart.name, base)
            message = self.render_diff_summary(chart, relative, base)
        self.github.emit('GITHUB_STEP_SUMMARY', message)

    def render_diff_summary(self, chart, relative, base):
        """Render the minimal example at base and HEAD and return a Markdown summary of the difference."""
        example = chart / 'examples' / 'minimal.yaml'
        with tempfile.TemporaryDirectory() as directory:
            worktree = Path(directory) / 'base'
            self.commands.run(['git', 'worktree', 'add', '--detach', worktree, base])
            try:
                self.helm.dependencies(relative, cwd=worktree)
                before = self.helm.render(relative, example, cwd=worktree)
                self.helm.dependencies(chart)
                after = self.helm.render(chart, example)
            finally:
                self.commands.run(['git', 'worktree', 'remove', '--force', worktree])
        diff = ''.join(difflib.unified_diff(
            before.splitlines(keepends=True), after.splitlines(keepends=True), fromfile='base', tofile='head',
        ))
        if not diff:
            return f'### Render diff: {chart.name}\nNo difference in the rendered output.\n'
        return f'### Render diff: {chart.name}\n```diff\n{diff}\n```\n'
