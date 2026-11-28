"""Tag untagged test methods with test_case decorators and render the test registry."""

import ast
import importlib.util
import inspect
import re
import sys
import unittest
from collections import defaultdict
from datetime import date
from pathlib import Path

import yaml


IMPORT_LINE = 'from helm_pipeline.testing.case import test_case'
ID_FORMAT = 'TC-{area}-{number:03d}'
ID_IN_DECORATOR = re.compile(r'TC-([A-Z]+)-(\d{3})')
AREAS_FILE = 'areas.yaml'
EXCEPTIONS_FILE = 'exceptions.yaml'
REGISTRY_FILE = 'REGISTRY.md'
DEFAULT_SCOPE = 'Unit'
EXCEPTION_FIELDS = ('id', 'reason', 'owner', 'expires')
# Area per test, in the areas file: `tests:` maps Class.method to an area code, for example
# tests:
#   KeycloakAdminTests.test_authentication_and_json_request: AUTH
# Test exclusions live in the `tests:` section of an exceptions file, next to the trivy and kubescape sections.
# Example, comment only (not a real file):
# tests:
#   - id: TC-KSC-003
#     reason: Exit codes are covered by the chart scan until this test is rewritten
#     owner: Platform team
#     expires: 2027-05-01


def derive_title(doc, name):
    """Return the title from the first docstring line, without the 'Test that' prefix and trailing dot."""
    if not doc:
        return name[len('test_'):].replace('_', ' ').capitalize()
    first = doc.strip().splitlines()[0].strip()
    if first.startswith('Test that '):
        first = first[len('Test that '):]
    first = first.rstrip('.')
    return first[:1].upper() + first[1:]


def default_area(file):
    """Return the area code and name derived from a test file name, used when no area is named for the file or test."""
    stem = Path(file).stem
    base = stem[len('test_'):] if stem.startswith('test_') else stem
    return re.sub(r'[^A-Za-z]', '', base).upper(), base.replace('_', ' ').capitalize()


def test_methods(tree):
    """Yield (class name, function node) for every test method of a TestCase class, in file order."""
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name.startswith('test_'):
                    yield node.name, item


def test_classes(module):
    """Yield every TestCase subclass defined in or imported into a module."""
    for value in vars(module).values():
        if isinstance(value, type) and issubclass(value, unittest.TestCase) and value is not unittest.TestCase:
            yield value


def load_module(path):
    """Import a test module from its file, with its folder on the import path, so its classes can be inspected."""
    if str(path.parent) not in sys.path:
        sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(f'registry_{path.stem}', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_case_decorator(function):
    """Return the test_case call of a test method, or None when it is untagged."""
    for decorator in function.decorator_list:
        if isinstance(decorator, ast.Call) and getattr(decorator.func, 'id', '') == 'test_case':
            return decorator
    return None


def load_areas(path):
    """Return the scope, the per-file areas and the per-test area codes of an areas file; defaults when absent."""
    if not path.is_file():
        return DEFAULT_SCOPE, {}, {}
    data = yaml.safe_load(path.read_text(encoding='utf-8')) or {}
    files = {file: (str(entry['code']), str(entry['name'])) for file, entry in (data.get('areas') or {}).items()}
    tests = {name: str(code) for name, code in (data.get('tests') or {}).items()}
    return str(data.get('scope', DEFAULT_SCOPE)), files, tests


class Tagger:
    """Tag the untagged tests of one test folder and regenerate its registry."""

    def __init__(self, tests):
        """Store the test folder and read its optional areas file.

        Args:
            tests: Folder with the test_*.py modules and, optionally, areas.yaml and exceptions.yaml.
        """
        self.tests = Path(tests).resolve()
        self.registry = self.tests / REGISTRY_FILE
        self.exceptions = self.tests / EXCEPTIONS_FILE
        self.scope, self.file_areas, self.test_areas = load_areas(self.tests / AREAS_FILE)

    def paths(self):
        """Return the test modules of the folder, sorted by name."""
        return sorted(self.tests.glob('test_*.py'))

    def area_for_test(self, path, class_name, function):
        """Return the area code of one test: its own entry, else its file's entry, else the file-name default."""
        key = f'{class_name}.{function.name}'
        if key in self.test_areas:
            return self.test_areas[key]
        if path.name in self.file_areas:
            return self.file_areas[path.name][0]
        return default_area(path.name)[0]

    def highest_numbers(self):
        """Return the highest tracking number used so far per area, so new IDs continue the sequence."""
        highest = defaultdict(int)
        for path in self.paths():
            for match in ID_IN_DECORATOR.finditer(path.read_text(encoding='utf-8')):
                highest[match.group(1)] = max(highest[match.group(1)], int(match.group(2)))
        return highest

    def tag_file(self, path, highest):
        """Add a test_case decorator to every untagged test of one file and return how many were tagged."""
        source = path.read_text(encoding='utf-8')
        newline = '\r\n' if '\r\n' in source else '\n'
        lines = source.split(newline)
        tree = ast.parse(source)
        decorators = {}
        for class_name, function in test_methods(tree):
            if test_case_decorator(function) is None:
                code = self.area_for_test(path, class_name, function)
                highest[code] += 1
                identifier = ID_FORMAT.format(area=code, number=highest[code])
                title = derive_title(ast.get_docstring(function), function.name)
                decorators[function.lineno - 1] = f"{' ' * function.col_offset}@test_case({identifier!r}, {title!r})"
        if not decorators:
            return 0
        result = []
        has_import = any(line.startswith('from ') and 'test_case' in line and 'import' in line for line in lines)
        last_import = max(node.end_lineno for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom)))
        for index, line in enumerate(lines):
            if index in decorators:
                result.append(decorators[index])
            result.append(line)
            if index == last_import - 1 and not has_import:
                result.append(IMPORT_LINE)
        path.write_text(newline.join(result), encoding='utf-8')
        return len(decorators)

    def registry_rows(self):
        """Return (id, title, file, test) for every tagged test, including tests inherited from CLI test classes."""
        rows = []
        for path in self.paths():
            classes = list(test_classes(load_module(path)))
            bases = {base for cls in classes for base in cls.__mro__[1:]}
            for cls in (cls for cls in classes if cls not in bases):
                for attribute in dir(cls):
                    method = getattr(cls, attribute)
                    identifier = getattr(method, 'test_id', None)
                    if attribute.startswith('test_') and identifier:
                        source = Path(inspect.getsourcefile(method)).name
                        rows.append((identifier, method.test_title, source, f'{cls.__name__}.{attribute}'))
        return sorted(rows)

    def load_exceptions(self, known_ids):
        """Return the validated test exclusions of the exceptions file, or an empty list when it is absent."""
        if not self.exceptions.is_file():
            return []
        data = yaml.safe_load(self.exceptions.read_text(encoding='utf-8')) or {}
        if not isinstance(data, dict):
            raise ValueError(f'{self.exceptions}: exceptions must be a mapping')
        entries = data.get('tests') or []
        if not isinstance(entries, list):
            raise ValueError(f'{self.exceptions}: tests must be a list')
        for entry in entries:
            if not isinstance(entry, dict):
                raise ValueError(f'{self.exceptions}: every exclusion must be a mapping')
            missing = [field for field in EXCEPTION_FIELDS if not str(entry.get(field, '')).strip()]
            if missing:
                raise ValueError(f'{self.exceptions}: exclusion {entry.get("id", "?")} is missing {", ".join(missing)}')
            if entry['id'] not in known_ids:
                raise ValueError(f'{self.exceptions}: unknown test id {entry["id"]}')
            date.fromisoformat(str(entry['expires']))
        return entries

    def area_names(self):
        """Return the name of each area code: from the areas file, else derived from the first file that uses it."""
        names = {}
        for code, name in self.file_areas.values():
            names.setdefault(code, name)
        for path in self.paths():
            code, name = default_area(path.name)
            names.setdefault(code, name)
        return names

    def render(self, rows, exceptions=()):
        """Return the Markdown text of the registry: a legend of the areas in use, the tests per area, and any exclusions."""
        names = self.area_names()
        files = defaultdict(set)
        for identifier, _, file, _ in rows:
            files[identifier.split('-')[1]].add(file)
        header = ('# Test registry\n\nGenerated from the `test_case` decorators in this folder. '
                  'Regenerate with `tag-tests`.\n\n')
        legend = ['## Legend', '',
                  'Each test has an ID in the form `TC-<AREA>-<NNN>`. `TC` is the tracking prefix, `AREA` is one of the codes '
                  'below, and `NNN` numbers the tests of that area.', '',
                  '| Area | Name | Source files |', '| --- | --- | --- |']
        legend += [f"| {code} | {names.get(code, code)} | {', '.join(sorted(files[code]))} |" for code in sorted(files)]
        legend += ['', f'Each area has its own table below. **Title** is the behaviour the test checks, **File** is the test module '
                   f'and **Test** is the class and method name. **Scope** is {self.scope} for the tests in this folder.']
        sections = []
        for code in sorted(files):
            table = ['| ID | Scope | Title | File | Test |', '| --- | --- | --- | --- | --- |']
            table += [f'| {identifier} | {self.scope} | {title} | {file} | {test} |'
                      for identifier, title, file, test in rows if identifier.split('-')[1] == code]
            sections.append(f'### {code} - {names.get(code, code)}\n\n' + '\n'.join(table) + '\n')
        exclusions = ''
        if exceptions:
            lines = ['| ID | Reason | Owner | Expires |', '| --- | --- | --- | --- |']
            lines += [f"| {entry['id']} | {entry['reason']} | {entry['owner']} | {entry['expires']} |" for entry in exceptions]
            exclusions = '\n\n## Exclusions\n\n' + '\n'.join(lines) + '\n'
        return header + '\n'.join(legend) + '\n\n## Tests\n\n' + '\n'.join(sections) + exclusions

    def run(self, check):
        """Tag the untagged tests and rewrite the registry, or with check report what is out of date.

        Args:
            check: When True, nothing is written; the return value is 1 when tests or the registry are out of date.

        Returns:
            The process exit code: 0 on success, 1 when out of date.
        """
        highest = self.highest_numbers()
        untagged = 0
        for path in self.paths():
            if check:
                untagged += sum(test_case_decorator(function) is None
                                for _, function in test_methods(ast.parse(path.read_text(encoding='utf-8'))))
            else:
                untagged += self.tag_file(path, highest)
        rows = self.registry_rows()
        text = self.render(rows, self.load_exceptions({identifier for identifier, _, _, _ in rows}))
        if check:
            stale = not self.registry.is_file() or self.registry.read_text(encoding='utf-8') != text
            if untagged or stale:
                print(f'{untagged} untagged test(s); registry stale: {stale}')
                return 1
            print(f'all {len(rows)} tests are tagged and the registry is current')
            return 0
        self.registry.write_text(text, encoding='utf-8')
        print(f'tagged {untagged} test(s); registry lists {len(rows)} test(s)')
        return 0
