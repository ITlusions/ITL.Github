import argparse
import difflib
import hashlib
import io
import json
import logging
import os
import re
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path

import yaml

from helm_pipeline.logging_config import configure_logging

LOGGER = logging.getLogger(__name__)
IGNORE_MARKER = '.ciignore'
# Paths that the docs and example validation job depends on.
DOCS_INPUTS = (
    'charts/', 'docs/', 'overrides/', 'scripts/', 'test/', 'plugins/helm-tests/',
    'mkdocs.yml', 'requirements-docs.txt', 'requirements-ci.txt', '.github/workflows/ci.yml',
)
# Requirement files whose installed packages the dependency audit checks.
DEPENDENCY_INPUTS = ('requirements-ci.txt', 'requirements-docs.txt', 'requirements-security.txt')
# Files every non-ignored chart must contain, checked on every CI run.
REQUIRED_FILES = ('Chart.yaml', 'values.yaml', 'examples/minimal.yaml', 'examples/full.yaml')
# Charts that are not standalone Helm charts and are therefore not linted.
SKIPPED_LINT_CHARTS = ('spotinfo-applications',)
HELM_REPOSITORIES = {
    'istio': 'https://istio-release.storage.googleapis.com/charts',
    'prometheus-community': 'https://prometheus-community.github.io/helm-charts',
    'stakater': 'https://stakater.github.io/stakater-charts',
    'csi': 'https://raw.githubusercontent.com/kubernetes-csi/csi-driver-nfs/master/charts',
    'headlamp': 'https://kubernetes-sigs.github.io/headlamp',
    'kubescape': 'https://kubescape.github.io/helm-charts/',
    'argo': 'https://argoproj.github.io/argo-helm',
    'kyverno': 'https://kyverno.github.io/kyverno/',
    'external-secrets': 'https://charts.external-secrets.io',
    'aquasecurity': 'https://aquasecurity.github.io/helm-charts/',
    'cilium': 'https://helm.cilium.io/',
    'metallb': 'https://metallb.github.io/metallb',
    'traefik': 'https://traefik.github.io/charts',
}
# Each download is (url, sha256); the checksum is verified before the archive is used.
KUBECONFORM_DOWNLOAD = (
    'https://github.com/yannh/kubeconform/releases/download/v0.7.0/kubeconform-linux-amd64.tar.gz',
    'c31518ddd122663b3f3aa874cfe8178cb0988de944f29c74a0b9260920d115d3',
)
HELM_UNITTEST_DOWNLOAD = (
    'https://github.com/helm-unittest/helm-unittest/releases/download/v1.2.1/helm-unittest-linux-amd64-1.2.1.tgz',
    '48e86ecc1467b009630e5954375e5d8494139f73b466df5fe8c04fa45b634939',
)
KIND_TOOLS = {
    'kind': (
        'https://github.com/kubernetes-sigs/kind/releases/download/v0.33.0/kind-linux-amd64',
        'aee6151561422756b764a4ae28e7f44cda5af5a9eead3cc9985112b1de8d8e0d',
    ),
    'kubectl': (
        'https://dl.k8s.io/release/v1.36.5/bin/linux/amd64/kubectl',
        '33bc88a24c3b09cf55bfd59e6ca977881b61fc3f25ab65bc80c65b430248648e',
    ),
}
CRD_SCHEMA_LOCATION = (
    'https://raw.githubusercontent.com/datreeio/CRDs-catalog/main/'
    '{{.Group}}/{{.ResourceKind}}_{{.ResourceAPIVersion}}.json'
)
SEMVER = re.compile(r'(\d+)\.(\d+)\.(\d+)')


def compact_json(value):
    """Serialize a value as compact JSON for GitHub Actions outputs."""
    return json.dumps(value, separators=(',', ':'))


def emit(env_name, text):
    """Append text to the file named by an environment variable, or print it when the variable is unset."""
    target = os.environ.get(env_name)
    if target:
        with Path(target).open('a', encoding='utf-8') as stream:
            stream.write(text)
    else:
        print(text, end='')


def add_to_github_path(directory):
    """Append a directory to GITHUB_PATH so that later workflow steps can run its binaries."""
    target = os.environ.get('GITHUB_PATH')
    if not target:
        raise ValueError('GITHUB_PATH is missing')
    with Path(target).open('a', encoding='utf-8') as stream:
        stream.write(f'{directory}\n')


class ChartPipeline:
    def __init__(self, root, runner=subprocess.run):
        self.root = Path(root).resolve()
        self.runner = runner

    def ignored(self, chart):
        """Return True when a chart directory contains the .ciignore marker file."""
        return (self.root / chart / IGNORE_MARKER).is_file()

    # AI generated code: GitHub Copilot Claude Haiku 5.5
    def log_ignored(self, charts):
        """Log each chart skipped by a .ciignore marker together with the marker's reason."""
        for chart in charts:
            if self.ignored(chart):
                reason = (self.root / chart / IGNORE_MARKER).read_text(encoding='utf-8').strip()
                LOGGER.info('Skipping %s: %s', chart, reason)

    def run(self, args, *, cwd=None, capture=False, check=True, input_text=None):
        command = [str(arg) for arg in args]
        LOGGER.info('Running %s', ' '.join(command))
        return self.runner(
            command, cwd=cwd or self.root, check=check,
            text=True, encoding='utf-8', capture_output=capture, input=input_text,
        )

    def metadata(self, chart):
        metadata = yaml.safe_load((chart / 'Chart.yaml').read_text(encoding='utf-8'))
        if not isinstance(metadata, dict):
            raise ValueError(f'{chart}: Chart.yaml must be a mapping')
        return metadata

    def add_repositories(self):
        for name, url in HELM_REPOSITORIES.items():
            self.run(['helm', 'repo', 'add', name, url, '--force-update'])
        self.run(['helm', 'repo', 'update'])

    def dependencies(self, chart, cwd=None):
        path = Path(chart)
        if not path.is_absolute():
            path = Path(cwd or self.root) / path
        command = 'build' if (path / 'Chart.lock').is_file() else 'update'
        if command == 'update' and self.metadata(path).get('dependencies'):
            LOGGER.warning('%s: Chart.lock is missing; dependencies are re-resolved', path.name)
        self.run(['helm', 'dependency', command, chart], cwd=cwd)

    def diff_paths(self, base, develop=None, pathspec=None):
        """Return the union of paths changed from base to HEAD and, when given, from base to develop."""
        targets = ['HEAD', develop] if develop else ['HEAD']
        paths = set()
        for target in targets:
            command = ['git', 'diff', '--name-only', base, target]
            if pathspec:
                command += ['--', pathspec]
            paths.update(self.run(command, capture=True).stdout.splitlines())
        return paths

    def changed(self, base, develop=None):
        if not base or base == '0' * 40:
            base = 'origin/main'
        changed_charts = set()
        for path in self.diff_paths(base, develop, 'charts/'):
            parts = path.split('/')
            is_chart_file = len(parts) >= 3 and parts[0] == 'charts'
            if is_chart_file and (self.root / 'charts' / parts[1] / 'Chart.yaml').is_file():
                changed_charts.add(f'charts/{parts[1]}')
        self.log_ignored(sorted(changed_charts))
        selected = sorted(name for name in changed_charts if not self.ignored(name))
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
        charts = {}
        for metadata_path in (self.root / 'charts').glob('*/Chart.yaml'):
            chart = metadata_path.parent
            metadata = self.metadata(chart)
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

    def chart_from_tag(self, tag):
        match = re.fullmatch(r'chart/([a-z0-9-]+)/v\d+\.\d+\.\d+', tag)
        if not match:
            raise ValueError(f'Tag does not have the form chart/<chart-name>/v<version>: {tag}')
        return match.group(1)

    def validated_chart(self, name):
        path = (self.root / 'charts' / name).resolve()
        if Path(name).name != name or path.parent != self.root / 'charts' or not (path / 'Chart.yaml').is_file():
            raise ValueError(f'Unknown chart: {name}')
        return f'charts/{name}'

    def chart_paths(self):
        """Return the repository path of every chart directory, sorted."""
        return sorted(f'charts/{path.parent.name}' for path in (self.root / 'charts').glob('*/Chart.yaml'))

    def all_charts(self):
        """Return every chart path that is not marked with a .ciignore file."""
        charts = self.chart_paths()
        self.log_ignored(charts)
        return [chart for chart in charts if not self.ignored(chart)]

    def write_changed(self, base, scan_all=False, selected_chart=None, tag=None, develop=None):
        if tag:
            selected_chart = self.chart_from_tag(tag)
        if selected_chart:
            base, charts = 'HEAD', []
            docs = dependencies = True
            affected = [self.validated_chart(selected_chart)]
            validate = affected
        else:
            # Full scans keep the diff base so render-diff and security scans still compare against the target branch.
            base, charts = self.changed(base, develop)
            paths = self.changed_paths(base, develop)
            docs = self.touches(paths, DOCS_INPUTS)
            dependencies = self.touches(paths, DEPENDENCY_INPUTS)
            if scan_all:
                docs = dependencies = True
                affected = self.all_charts()
            else:
                expanded = self.affected_charts(charts)
                self.log_ignored(sorted(set(expanded) - set(charts)))
                affected = [chart for chart in expanded if not self.ignored(chart)]
            validate = self.all_charts()
        LOGGER.info('Affected charts: %s', ', '.join(affected) or 'none')
        outputs = {
            'charts': compact_json(charts),
            'affected': compact_json(affected),
            'base': base,
            'docs': str(docs).lower(),
            'dependencies': str(dependencies).lower(),
            'validate': compact_json(validate),
        }
        emit('GITHUB_OUTPUT', ''.join(f'{key}={value}\n' for key, value in outputs.items()))

    def check_version(self, chart, registry=None):
        """Check that the chart declares a version and, when a registry is given, that it is not published yet."""
        chart = Path(chart).resolve()
        version = str(self.metadata(chart).get('version', ''))
        if not version:
            raise ValueError(f'{chart.name}: chart version is missing')
        if registry:
            result = self.run([
                'helm', 'show', 'chart', f'oci://{registry}/charts/{chart.name}', '--version', version,
            ], capture=True, check=False)
            if result.returncode == 0:
                raise ValueError(f'{chart.name} {version} already exists in the registry')
            error = (result.stderr or '').lower()
            reference = f'{registry}/charts/{chart.name}:{version}'.lower()
            if not any(marker in error for marker in ('manifest unknown', '404 not found', f'{reference}: not found')):
                raise RuntimeError(f'Registry check failed: {result.stderr}')
            LOGGER.info('%s %s is not published to %s yet', chart.name, version, registry)

    def released_version(self, chart):
        """Return the next release version: the highest chart tag bumped by one patch, never below Chart.yaml."""
        # AI generated code: GitHub Copilot Claude Haiku 5.5
        metadata = self.metadata(chart)
        name = metadata.get('name', chart.name)
        floor = tuple(int(part) for part in SEMVER.fullmatch(str(metadata.get('version', ''))).groups())
        prefix = f'chart/{name}/v'
        tags = self.run(['git', 'tag', '--list', f'{prefix}*'], capture=True).stdout.split()
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
        # AI generated code: GitHub Copilot Claude Haiku 5.5
        chart = Path(chart).resolve()
        release = self.released_version(chart)
        name = self.metadata(chart).get('name', chart.name)
        if ref == 'refs/heads/main':
            version, is_release, tag = release, 'true', f'chart/{name}/v{release}'
        else:
            branch = ref.removeprefix('refs/heads/')
            slug = re.sub(r'[^a-z0-9]+', '-', branch.lower()).strip('-')
            version, is_release, tag = f'{release}-{slug}.{run_number}-{sha[:7]}', 'false', ''
        emit('GITHUB_OUTPUT', f'version={version}\nis-release={is_release}\ntag={tag}\n')
        LOGGER.info('Version for %s: %s (release: %s)', name, version, is_release)
        return version

    def render(self, chart, values, cwd=None):
        """Return the manifests that Helm renders for a chart with the given values file."""
        return self.run([
            'helm', 'template', 'test', chart, '--namespace', 'operators', '--values', values,
        ], cwd=cwd, capture=True).stdout

    def render_diff(self, chart, base):
        chart = Path(chart).resolve()
        relative = chart.relative_to(self.root).as_posix()
        if self.run(['git', 'cat-file', '-e', f'{base}:{relative}/Chart.yaml'], capture=True, check=False).returncode:
            message = f'{chart.name} does not exist in {base}; no comparison\n'
        elif self.metadata(chart).get('type') == 'library':
            message = f'{chart.name} is a library chart; no render diff\n'
        else:
            LOGGER.info('Rendering %s against %s', chart.name, base)
            message = self.render_diff_summary(chart, relative, base)
        emit('GITHUB_STEP_SUMMARY', message)

    def render_diff_summary(self, chart, relative, base):
        """Render the minimal example at base and HEAD and return a Markdown summary of the difference."""
        example = chart / 'examples' / 'minimal.yaml'
        with tempfile.TemporaryDirectory() as directory:
            worktree = Path(directory) / 'base'
            self.run(['git', 'worktree', 'add', '--detach', worktree, base])
            try:
                self.dependencies(relative, cwd=worktree)
                before = self.render(relative, example, cwd=worktree)
                self.dependencies(chart)
                after = self.render(chart, example)
            finally:
                self.run(['git', 'worktree', 'remove', '--force', worktree])
        diff = ''.join(difflib.unified_diff(before.splitlines(keepends=True), after.splitlines(keepends=True),
                                            fromfile='base', tofile='head'))
        if not diff:
            return f'### Render diff: {chart.name}\nNo difference in the rendered output.\n'
        return f'### Render diff: {chart.name}\n```diff\n{diff}\n```\n'

    def lint_all(self):
        self.add_repositories()
        for metadata in sorted((self.root / 'charts').glob('*/Chart.yaml')):
            chart = metadata.parent
            if chart.name in SKIPPED_LINT_CHARTS:
                continue
            LOGGER.info('Linting %s', chart.name)
            self.dependencies(chart)
            self.run(['helm', 'lint', chart])

    def publish(self, chart, registry, username, password):
        if not registry or not username or not password:
            raise ValueError('Registry, username and password are required')
        chart = Path(chart).resolve()
        self.run(['helm', 'registry', 'login', registry, '-u', username, '--password-stdin'], input_text=password + '\n')
        self.check_version(chart, registry=registry)
        self.add_repositories()
        self.dependencies(chart)
        with tempfile.TemporaryDirectory() as directory:
            self.run(['helm', 'package', chart, '--destination', directory])
            packages = list(Path(directory).glob('*.tgz'))
            if len(packages) != 1:
                raise ValueError(f'{chart.name}: expected exactly one chart package')
            LOGGER.info('Pushing %s to %s', packages[0].name, registry)
            self.run(['helm', 'push', packages[0], f'oci://{registry}/charts'])

    def package(self, chart, destination):
        """Build dependencies, lint, and package one chart into the destination directory."""
        # AI generated code: GitHub Copilot Claude Haiku 5.5
        chart = Path(chart).resolve()
        destination = Path(destination).resolve()
        destination.mkdir(parents=True, exist_ok=True)
        self.dependencies(chart)
        self.run(['helm', 'lint', chart])
        self.run(['helm', 'package', chart, '--destination', destination])
        packages = sorted(destination.glob(f'{chart.name}-*.tgz'))
        if len(packages) != 1:
            raise ValueError(f'{chart.name}: expected exactly one chart package in {destination}')
        LOGGER.info('Packaged %s', packages[0].name)
        return packages[0]

    def setup_tools(self, directory):
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        # Binaries restored from the CI cache are reused; only missing tools are downloaded and verified.
        if not (directory / 'kubeconform').is_file():
            archive = self.download_verified(*KUBECONFORM_DOWNLOAD)
            self.extract_members(archive, directory, ('kubeconform',))
        add_to_github_path(directory)
        plugins = self.run(['helm', 'env', 'HELM_PLUGINS'], capture=True).stdout.strip()
        if not plugins:
            raise ValueError('Helm plugin directory is missing')
        unittest_directory = Path(plugins) / 'unittest'
        if not (unittest_directory / 'untt-linux-amd64').is_file():
            archive = self.download_verified(*HELM_UNITTEST_DOWNLOAD)
            self.extract_members(archive, unittest_directory, ('plugin.yaml', 'untt-linux-amd64'))

    def setup_kind(self, directory):
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        add_to_github_path(directory)
        for name, (url, checksum) in KIND_TOOLS.items():
            binary = directory / name
            if binary.is_file():
                continue
            binary.write_bytes(self.download_verified(url, checksum))
            binary.chmod(0o755)

    def download_verified(self, url, expected):
        LOGGER.info('Downloading %s', url)
        with urllib.request.urlopen(url, timeout=120) as response:
            data = response.read()
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError(f'Checksum does not match: {url}')
        LOGGER.info('Checksum verified for %s', url)
        return data

    def extract_members(self, data, destination, members):
        destination.mkdir(parents=True, exist_ok=True)
        with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as archive:
            for name in members:
                member = archive.getmember(name)
                if not member.isfile():
                    raise ValueError(f'{name} is not a regular file')
                source = archive.extractfile(member)
                if source is None:
                    raise ValueError(f'{name} is missing from the archive')
                target = destination / name
                target.write_bytes(source.read())
                if name != 'plugin.yaml':
                    target.chmod(0o755)

    def missing_requirements(self, chart):
        """Return the required files that a chart directory lacks."""
        return [name for name in REQUIRED_FILES if not (self.root / chart / name).exists()]

    def check_requirements(self):
        """Raise when any non-ignored chart lacks a required file."""
        failures = {}
        charts = self.chart_paths()
        self.log_ignored(charts)
        checked = [chart for chart in charts if not self.ignored(chart)]
        LOGGER.info('Checking %d chart(s) for %d required file(s) each (%s): %s',
                    len(checked), len(REQUIRED_FILES), ', '.join(REQUIRED_FILES), ', '.join(checked) or 'none')
        for chart in checked:
            missing = self.missing_requirements(chart)
            if missing:
                failures[chart] = missing
                LOGGER.error('%s: missing required file(s): %s', chart, ', '.join(missing))
            else:
                LOGGER.info('%s: all required files present', chart)
        if failures:
            LOGGER.error('%d of %d chart(s) do not meet the requirements', len(failures), len(checked))
            raise ValueError(f'{len(failures)} chart(s) do not meet the requirements')
        LOGGER.info('All %d non-ignored chart(s) meet the requirements', len(checked))

    def validate(self, chart):
        chart = Path(chart).resolve()
        metadata = self.metadata(chart)
        self.dependencies(chart)
        for example in ('minimal', 'full'):
            self.run(['helm', 'lint', chart, '--values', chart / 'examples' / f'{example}.yaml'])

        tests = chart / 'tests'
        if tests.is_dir() and any(tests.rglob('*_test.yaml')):
            self.run(['helm', 'unittest', chart])
        if tests.is_dir() and any(tests.rglob('test_*.py')):
            self.run([sys.executable, '-m', 'unittest', 'discover', '-s', tests, '-p', 'test_*.py', '-v'])

        if metadata.get('type') == 'library':
            LOGGER.info('%s is a library chart: render test skipped', chart.name)
            return

        output_dir = self.root / 'dist' / 'render'
        output_dir.mkdir(parents=True, exist_ok=True)
        for example in ('minimal', 'full'):
            rendered = self.render(chart, chart / 'examples' / f'{example}.yaml')
            resources = [resource for resource in yaml.safe_load_all(rendered) if resource]
            if not resources or not all(isinstance(resource, dict) and resource.get('kind') for resource in resources):
                raise ValueError(f'{chart.name}: {example} renders no valid resources')
            output = output_dir / f'{chart.name}-{example}.yaml'
            output.write_text(rendered, encoding='utf-8')
            self.run([
                'kubeconform', '-summary', '-schema-location', 'default',
                '-schema-location', CRD_SCHEMA_LOCATION, '-skip', 'CustomResourceDefinition', output,
            ])


def main():
    parser = argparse.ArgumentParser(description='SpotINFO Helm chart CI')
    commands = parser.add_subparsers(dest='command', required=True)
    changed = commands.add_parser('changed')
    changed.add_argument('--base', default=os.environ.get('BASE_SHA', ''))
    changed.add_argument('--all', action='store_true', default=os.environ.get('SCAN_ALL') == '1')
    changed.add_argument('--chart', default=os.environ.get('SCAN_CHART'))
    changed.add_argument('--tag', default=os.environ.get('RELEASE_TAG') or None)
    changed.add_argument('--develop', default=None)
    commands.add_parser('setup-tools').add_argument('--directory', required=True)
    commands.add_parser('setup-kind').add_argument('--directory', required=True)
    commands.add_parser('lint-all')
    commands.add_parser('check-requirements')
    commands.add_parser('validate').add_argument('chart', nargs='?', default=os.environ.get('CHART'))
    commands.add_parser('check-version').add_argument('chart', nargs='?', default=os.environ.get('CHART'))
    commands.add_parser('next-version').add_argument('chart', nargs='?', default=os.environ.get('CHART'))
    diff = commands.add_parser('render-diff')
    diff.add_argument('chart', nargs='?', default=os.environ.get('CHART'))
    diff.add_argument('base', nargs='?', default=os.environ.get('BASE_SHA'))
    commands.add_parser('publish').add_argument('chart', nargs='?', default=os.environ.get('CHART'))
    package = commands.add_parser('package')
    package.add_argument('chart', nargs='?', default=os.environ.get('CHART'))
    package.add_argument('--destination', default='dist/packages')
    args = parser.parse_args()
    configure_logging()
    if args.command in ('validate', 'check-version', 'next-version', 'render-diff', 'publish', 'package') and not args.chart:
        parser.error('chart or CHART is required')
    if args.command == 'render-diff' and not args.base:
        parser.error('base or BASE_SHA is required')
    ci = ChartPipeline(Path.cwd())
    if args.command == 'changed':
        ci.write_changed(args.base, scan_all=args.all, selected_chart=args.chart, tag=args.tag, develop=args.develop)
    elif args.command == 'setup-tools':
        ci.setup_tools(args.directory)
    elif args.command == 'setup-kind':
        ci.setup_kind(args.directory)
    elif args.command == 'lint-all':
        ci.lint_all()
    elif args.command == 'check-requirements':
        ci.check_requirements()
    elif args.command == 'validate':
        ci.add_repositories()
        ci.validate(args.chart)
    elif args.command == 'check-version':
        ci.check_version(args.chart)
    elif args.command == 'next-version':
        ci.next_version(args.chart, os.environ.get('GITHUB_REF', ''), os.environ.get('GITHUB_RUN_NUMBER', '0'),
                        os.environ.get('GITHUB_SHA', ''))
    elif args.command == 'render-diff':
        ci.add_repositories()
        ci.render_diff(args.chart, args.base)
    elif args.command == 'package':
        ci.add_repositories()
        ci.package(args.chart, args.destination)
    elif args.command == 'publish':
        ci.publish(args.chart, os.environ.get('REGISTRY_HOST'), os.environ.get('REGISTRY_USERNAME'),
                   os.environ.get('REGISTRY_PASSWORD'))


if __name__ == '__main__':
    main()