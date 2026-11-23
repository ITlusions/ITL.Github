"""Write results to the files that GitHub Actions exposes through environment variables."""

import os
from pathlib import Path


class GitHubFiles:
    """Append outputs, job summaries, and PATH entries to the GitHub Actions files."""

    def emit(self, variable, text):
        """Append text to the file named by an environment variable, or print it when the variable is unset."""
        target = os.environ.get(variable)
        if target:
            with Path(target).open('a', encoding='utf-8') as stream:
                stream.write(text)
        else:
            print(text, end='')

    def append_table(self, title, headers, rows):
        """Add a Markdown table to the job summary; nothing is written outside GitHub Actions."""
        summary = os.environ.get('GITHUB_STEP_SUMMARY')
        if not summary:
            return
        lines = [f'### {title}', '', '| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join(['---'] * len(headers)) + ' |']
        lines.extend('| ' + ' | '.join(str(cell) for cell in row) + ' |' for row in rows)
        with Path(summary).open('a', encoding='utf-8') as stream:
            stream.write('\n'.join(lines) + '\n\n')

    def add_to_path(self, directory):
        """Append a directory to GITHUB_PATH so that later workflow steps can run its binaries."""
        target = os.environ.get('GITHUB_PATH')
        if not target:
            raise ValueError('GITHUB_PATH is missing')
        with Path(target).open('a', encoding='utf-8') as stream:
            stream.write(f'{directory}\n')
