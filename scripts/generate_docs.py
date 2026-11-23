"""Generate the Jekyll reference pages and data files for reusable workflows and composite actions.

The generator reads ``.github/workflows/_managed-*.yml`` and ``actions/*/action.yml`` so the
documentation always matches the code. Output goes to ``docs/reference`` and
``docs/_data/generated``. Both are git-ignored and rebuilt on every Pages deployment.

Run from the repository root with ``python scripts/generate_docs.py``.
"""

from __future__ import annotations

import json
import operator
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
REPO_SLUG = "ITlusions/ITL.Github"
WORKFLOW_PREFIX = "_managed-"

WORKFLOW_CATEGORY_ORDER = (
    "Python",
    "Docker",
    "Helm",
    "Claude plugins",
    "Versioning and releases",
    "Quality",
    "Other",
)

# Workflow slug (file name without the managed prefix and extension) to category.
WORKFLOW_CATEGORIES = {
    "python-ci": "Python",
    "python-publish": "Python",
    "ci-python": "Python",
    "publish-pypi": "Python",
    "ci-docker": "Docker",
    "docker-build": "Docker",
    "docker-retag": "Docker",
    "helm-ci": "Helm",
    "helm-pipeline": "Helm",
    "helm-publish": "Helm",
    "helm-security": "Helm",
    "claude-plugin-release": "Claude plugins",
    "claude-plugin-version-tag": "Claude plugins",
    "claude-plugins-ci": "Claude plugins",
    "claude-plugins-publish": "Claude plugins",
    "detect-version": "Versioning and releases",
    "auto-tag": "Versioning and releases",
    "float-tags": "Versioning and releases",
    "release-gh": "Versioning and releases",
    "check-deadlinks": "Quality",
    "validate-actions": "Quality",
}

# Legacy workflow slug to the slug of its replacement.
SUPERSEDED_BY = {
    "ci-python": "python-ci",
    "publish-pypi": "python-publish",
}


@dataclass(frozen=True)
class Parameter:
    """A declared input, secret, or output of a workflow or action."""

    name: str
    description: str
    type_name: str = ""
    required: bool = False
    default: Any = None


@dataclass(frozen=True)
class ReusableWorkflow:
    """A `_managed-*` workflow that exposes a `workflow_call` interface."""

    file_name: str
    title: str
    description: str
    category: str
    inputs: tuple[Parameter, ...]
    secrets: tuple[Parameter, ...]
    outputs: tuple[Parameter, ...]

    @property
    def slug(self) -> str:
        """Return the file name without the managed prefix and extension."""
        return self.file_name.removeprefix(WORKFLOW_PREFIX).removesuffix(".yml")

    @property
    def superseded_by(self) -> str:
        """Return the slug of the replacement workflow, or an empty string."""
        return SUPERSEDED_BY.get(self.slug, "")


@dataclass(frozen=True)
class CompositeAction:
    """A composite action defined in `actions/<slug>/action.yml`."""

    slug: str
    title: str
    description: str
    inputs: tuple[Parameter, ...]
    outputs: tuple[Parameter, ...]


class SpecParser:
    """Reads workflow and action YAML declarations into domain objects."""

    def parse_workflow(self, path: Path) -> ReusableWorkflow | None:
        """Return the parsed workflow, or None when it has no `workflow_call` trigger.

        Args:
            path: Path to a `_managed-*.yml` workflow file.

        Returns:
            The parsed workflow, or None when the file is not reusable.
        """
        text = path.read_text(encoding="utf-8")
        document = yaml.safe_load(text) or {}
        # YAML 1.1 parses the bare `on` key as boolean True.
        trigger = document.get("on", document.get(True))
        if not isinstance(trigger, dict) or "workflow_call" not in trigger:
            return None
        interface = trigger["workflow_call"] or {}
        slug = path.name.removeprefix(WORKFLOW_PREFIX).removesuffix(".yml")
        return ReusableWorkflow(
            file_name=path.name,
            title=re.sub(r"\s*\(reusable\)\s*$", "", str(document.get("name", slug))),
            description=self._header_description(text),
            category=WORKFLOW_CATEGORIES.get(slug, "Other"),
            inputs=self._parameters(interface.get("inputs")),
            secrets=self._parameters(interface.get("secrets")),
            outputs=self._parameters(interface.get("outputs")),
        )

    def parse_action(self, path: Path) -> CompositeAction:
        """Return the parsed composite action.

        Args:
            path: Path to an `action.yml` file inside an action directory.

        Returns:
            The parsed composite action.
        """
        document = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return CompositeAction(
            slug=path.parent.name,
            title=str(document.get("name", path.parent.name)),
            description=self._one_line(document.get("description", "")),
            inputs=self._parameters(document.get("inputs")),
            outputs=self._parameters(document.get("outputs")),
        )

    def _header_description(self, text: str) -> str:
        """Return the first meaningful comment line above the first key of a workflow file.

        Args:
            text: Raw workflow file content.

        Returns:
            The first comment line, or an empty string when the header has none.
        """
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("name:"):
                continue
            if not line.startswith("#"):
                break
            content = line.lstrip("#").strip()
            if content and set(content) != {"-"}:
                return content
        return ""

    def _parameters(self, mapping: Any) -> tuple[Parameter, ...]:
        """Convert a YAML mapping of declarations into parameters in declaration order.

        Args:
            mapping: The `inputs`, `secrets`, or `outputs` mapping, or None.

        Returns:
            The declared parameters.
        """
        if not isinstance(mapping, dict):
            return ()
        parameters = []
        for name, declaration in mapping.items():
            spec = declaration or {}
            parameters.append(
                Parameter(
                    name=str(name),
                    description=self._one_line(spec.get("description", "")),
                    type_name=str(spec.get("type", "")),
                    required=bool(spec.get("required", False)),
                    default=spec.get("default"),
                )
            )
        return tuple(parameters)

    def _one_line(self, text: Any) -> str:
        """Collapse whitespace so a description fits on one table row.

        Args:
            text: Any YAML scalar.

        Returns:
            The text with all whitespace runs replaced by single spaces.
        """
        return " ".join(str(text).split())


class MarkdownRenderer:
    """Renders Jekyll Markdown pages from parsed workflow and action specs."""

    def workflow_page(self, workflow: ReusableWorkflow) -> str:
        """Return the reference page for one reusable workflow.

        Args:
            workflow: The workflow to document.

        Returns:
            The complete page content, including front matter.
        """
        lines = [f"# {workflow.title}", ""]
        if workflow.superseded_by:
            lines.append(
                f"> **Legacy:** superseded by [{workflow.superseded_by}]({workflow.superseded_by}.html). "
                "Use that workflow for new projects."
            )
            lines.append("")
        if workflow.description:
            lines.extend([workflow.description, ""])
        lines.extend([f"**File:** `.github/workflows/{workflow.file_name}`", ""])
        lines.extend(["## Usage", ""])
        lines.extend(self._code_block("yaml", self._workflow_usage(workflow)))
        lines.extend(self._section("Inputs", workflow.inputs, "input", "This workflow takes no inputs."))
        lines.extend(self._section("Secrets", workflow.secrets, "secret", "This workflow takes no secrets."))
        lines.extend(self._section("Outputs", workflow.outputs, "output", "This workflow has no outputs."))
        return self._document(workflow.title, workflow.description, lines)

    def action_page(self, action: CompositeAction) -> str:
        """Return the reference page for one composite action.

        Args:
            action: The action to document.

        Returns:
            The complete page content, including front matter.
        """
        lines = [f"# {action.title}", ""]
        if action.description:
            lines.extend([action.description, ""])
        lines.extend([f"**File:** `actions/{action.slug}/action.yml`", ""])
        lines.extend(["## Usage", ""])
        lines.extend(self._code_block("yaml", self._action_usage(action)))
        lines.extend(self._section("Inputs", action.inputs, "input", "This action takes no inputs."))
        lines.extend(self._section("Outputs", action.outputs, "output", "This action has no outputs."))
        return self._document(action.title, action.description, lines)

    def workflow_index(self, groups: list[tuple[str, list[ReusableWorkflow]]]) -> str:
        """Return the overview page that lists workflows per category.

        Args:
            groups: Category names with their workflows, in display order.

        Returns:
            The complete page content, including front matter.
        """
        lines = [
            "# Reusable workflows",
            "",
            f"Call a workflow with `uses: {REPO_SLUG}/.github/workflows/<file>@main`.",
            "",
        ]
        for name, members in groups:
            lines.extend([f"## {name}", "", "| Workflow | File | Description |", "|---|---|---|"])
            for workflow in members:
                legacy = " (legacy)" if workflow.superseded_by else ""
                lines.append(
                    f"| [{self._escape(workflow.title)}{legacy}]({workflow.slug}.html) "
                    f"| `{workflow.file_name}` | {self._escape(workflow.description)} |"
                )
            lines.append("")
        return self._document("Reusable workflows", "Reference for all reusable workflows", lines)

    def action_index(self, actions: list[CompositeAction]) -> str:
        """Return the overview page that lists composite actions.

        Args:
            actions: The actions to list.

        Returns:
            The complete page content, including front matter.
        """
        lines = [
            "# Composite actions",
            "",
            f"Call an action with `uses: {REPO_SLUG}/actions/<name>@main`.",
            "",
            "| Action | Description |",
            "|---|---|",
        ]
        for action in actions:
            lines.append(f"| [{self._escape(action.title)}]({action.slug}.html) | {self._escape(action.description)} |")
        lines.append("")
        return self._document("Composite actions", "Reference for all composite actions", lines)

    def _document(self, title: str, description: str, body: list[str]) -> str:
        """Wrap body lines in front matter and a raw block so Liquid does not parse `${{ }}` expressions.

        Args:
            title: Page title.
            description: Page description, falls back to the title.
            body: Markdown body lines.

        Returns:
            The complete page content.
        """
        front_matter = [
            "---",
            "layout: default",
            f"title: {json.dumps(title)}",
            f"description: {json.dumps(description or title)}",
            "---",
            "{% raw %}",
        ]
        return "\n".join(front_matter + [""] + body + ["{% endraw %}", ""])

    def _section(self, heading: str, parameters: tuple[Parameter, ...], mode: str, empty_text: str) -> list[str]:
        """Return a heading followed by a parameter table, or a sentence when there are none.

        Args:
            heading: Section heading.
            parameters: Parameters to list.
            mode: One of `input`, `secret`, or `output`, which selects the table columns.
            empty_text: Sentence shown when there are no parameters.

        Returns:
            Markdown lines for the section.
        """
        if not parameters:
            return [f"## {heading}", "", empty_text, ""]
        return [f"## {heading}", "", *self._table(parameters, mode), ""]

    def _table(self, parameters: tuple[Parameter, ...], mode: str) -> list[str]:
        """Return a Markdown table for the parameters.

        Args:
            parameters: Parameters to list.
            mode: One of `input`, `secret`, or `output`.

        Returns:
            Markdown table lines.
        """
        if mode == "input":
            header = ["Name", "Type", "Required", "Default", "Description"]
        elif mode == "secret":
            header = ["Name", "Required", "Description"]
        else:
            header = ["Name", "Description"]
        lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
        for parameter in parameters:
            lines.append("| " + " | ".join(self._cells(parameter, mode)) + " |")
        return lines

    def _cells(self, parameter: Parameter, mode: str) -> list[str]:
        """Return the table cells for one parameter.

        Args:
            parameter: The parameter to render.
            mode: One of `input`, `secret`, or `output`.

        Returns:
            The cell values in column order.
        """
        name = f"`{parameter.name}`"
        required = "yes" if parameter.required else "no"
        description = self._escape(parameter.description)
        if mode == "input":
            return [
                name,
                self._escape(parameter.type_name) or "-",
                required,
                self._escape(self._format_default(parameter.default)),
                description,
            ]
        if mode == "secret":
            return [name, required, description]
        return [name, description]

    def _format_default(self, value: Any) -> str:
        """Return a readable default value for a table cell.

        Args:
            value: The declared default.

        Returns:
            The default as an inline-code string, or `-` when there is none.
        """
        if value is None:
            return "-"
        if isinstance(value, bool):
            return f"`{'true' if value else 'false'}`"
        if value == "":
            return '`""`'
        return f"`{value}`"

    def _workflow_usage(self, workflow: ReusableWorkflow) -> list[str]:
        """Return a minimal calling job for a workflow.

        Args:
            workflow: The workflow to call.

        Returns:
            YAML lines that include every required input.
        """
        lines = [
            "jobs:",
            "  call:",
            f"    uses: {REPO_SLUG}/.github/workflows/{workflow.file_name}@main",
        ]
        lines.extend(self._with_block([p for p in workflow.inputs if p.required], "    "))
        if workflow.secrets:
            lines.append("    secrets: inherit")
        return lines

    def _action_usage(self, action: CompositeAction) -> list[str]:
        """Return a minimal step for a composite action.

        Args:
            action: The action to call.

        Returns:
            YAML lines that include every required input.
        """
        lines = ["steps:", f"  - uses: {REPO_SLUG}/actions/{action.slug}@main"]
        lines.extend(self._with_block([p for p in action.inputs if p.required], "    "))
        return lines

    def _with_block(self, parameters: list[Parameter], indent: str) -> list[str]:
        """Return a `with:` block for the given parameters, or no lines when there are none.

        Args:
            parameters: Parameters to pass.
            indent: Indentation of the `with:` key.

        Returns:
            YAML lines.
        """
        if not parameters:
            return []
        lines = [f"{indent}with:"]
        for parameter in parameters:
            lines.append(f"{indent}  {parameter.name}: {self._yaml_value(parameter)}")
        return lines

    def _yaml_value(self, parameter: Parameter) -> str:
        """Return a YAML literal for a parameter's default, or a placeholder when it has none.

        Args:
            parameter: The parameter to render.

        Returns:
            A YAML scalar.
        """
        value = parameter.default
        if value is None:
            return json.dumps(f"<{parameter.name}>")
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (int, float)):
            return str(value)
        return json.dumps(str(value))

    def _code_block(self, language: str, lines: list[str]) -> list[str]:
        """Wrap lines in a fenced code block.

        Args:
            language: Language tag for the fence.
            lines: Code lines.

        Returns:
            Markdown lines.
        """
        return [f"```{language}", *lines, "```", ""]

    def _escape(self, text: str) -> str:
        """Escape pipes so text can sit inside a Markdown table cell.

        Args:
            text: Cell text.

        Returns:
            The escaped text.
        """
        return str(text).replace("|", "\\|")


class DocsGenerator:
    """Discovers workflows and actions and writes the reference pages and data files."""

    def __init__(self, repo_root: Path, parser: SpecParser, renderer: MarkdownRenderer) -> None:
        """Store the repository root and collaborators.

        Args:
            repo_root: Repository root containing `.github/`, `actions/`, and `docs/`.
            parser: Reads the YAML declarations.
            renderer: Renders the Markdown output.
        """
        self._repo_root = repo_root
        self._parser = parser
        self._renderer = renderer
        self._reference_dir = repo_root / "docs" / "reference"
        self._data_dir = repo_root / "docs" / "_data" / "generated"

    def run(self) -> None:
        """Regenerate all reference pages and data files from scratch."""
        workflows = self._discover_workflows()
        actions = self._discover_actions()
        self._reset_outputs()
        self._write_workflow_pages(workflows)
        self._write_action_pages(actions)
        self._write_data(workflows, actions)
        print(f"Generated {len(workflows)} workflow pages and {len(actions)} action pages.")

    def _discover_workflows(self) -> list[ReusableWorkflow]:
        """Return all reusable workflows, sorted by title.

        Returns:
            The parsed workflows.
        """
        workflows = []
        for path in sorted((self._repo_root / ".github" / "workflows").glob(f"{WORKFLOW_PREFIX}*.yml")):
            workflow = self._parser.parse_workflow(path)
            if workflow is not None:
                workflows.append(workflow)
        workflows.sort(key=operator.attrgetter("title"))
        return workflows

    def _discover_actions(self) -> list[CompositeAction]:
        """Return all composite actions, sorted by title.

        Returns:
            The parsed actions.
        """
        actions = [self._parser.parse_action(path) for path in sorted((self._repo_root / "actions").glob("*/action.yml"))]
        actions.sort(key=operator.attrgetter("title"))
        return actions

    def _reset_outputs(self) -> None:
        """Delete the previous generated output so removed workflows do not linger."""
        shutil.rmtree(self._reference_dir, ignore_errors=True)
        shutil.rmtree(self._data_dir, ignore_errors=True)

    def _write_workflow_pages(self, workflows: list[ReusableWorkflow]) -> None:
        """Write one page per workflow plus the overview page.

        Args:
            workflows: Workflows to document.
        """
        directory = self._reference_dir / "workflows"
        for workflow in workflows:
            self._write_text(directory / f"{workflow.slug}.md", self._renderer.workflow_page(workflow))
        self._write_text(directory / "index.md", self._renderer.workflow_index(self._group_workflows(workflows)))

    def _write_action_pages(self, actions: list[CompositeAction]) -> None:
        """Write one page per action plus the overview page.

        Args:
            actions: Actions to document.
        """
        directory = self._reference_dir / "actions"
        for action in actions:
            self._write_text(directory / f"{action.slug}.md", self._renderer.action_page(action))
        self._write_text(directory / "index.md", self._renderer.action_index(actions))

    def _write_data(self, workflows: list[ReusableWorkflow], actions: list[CompositeAction]) -> None:
        """Write the data files that drive the landing page.

        Args:
            workflows: Workflows to describe.
            actions: Actions to describe.
        """
        workflow_data = {
            "count": len(workflows),
            "categories": [self._category_entry(name, members) for name, members in self._group_workflows(workflows)],
        }
        action_data = {"count": len(actions), "actions": [self._action_entry(action) for action in actions]}
        self._write_text(self._data_dir / "workflows.yml", yaml.safe_dump(workflow_data, sort_keys=False, allow_unicode=True))
        self._write_text(self._data_dir / "actions.yml", yaml.safe_dump(action_data, sort_keys=False, allow_unicode=True))

    def _group_workflows(self, workflows: list[ReusableWorkflow]) -> list[tuple[str, list[ReusableWorkflow]]]:
        """Group workflows by category in the configured display order, omitting empty categories.

        Args:
            workflows: Workflows to group.

        Returns:
            Category name and its workflows, in display order.
        """
        groups = []
        for name in WORKFLOW_CATEGORY_ORDER:
            members = [workflow for workflow in workflows if workflow.category == name]
            if members:
                groups.append((name, members))
        return groups

    def _category_entry(self, name: str, members: list[ReusableWorkflow]) -> dict[str, Any]:
        """Return the data entry for one workflow category.

        Args:
            name: Category name.
            members: Workflows in the category.

        Returns:
            A mapping ready for YAML serialization.
        """
        return {"name": name, "workflows": [self._workflow_entry(workflow) for workflow in members]}

    def _workflow_entry(self, workflow: ReusableWorkflow) -> dict[str, Any]:
        """Return the data entry for one workflow.

        Args:
            workflow: The workflow to describe.

        Returns:
            A mapping ready for YAML serialization.
        """
        return {
            "title": workflow.title,
            "slug": workflow.slug,
            "url": f"reference/workflows/{workflow.slug}.html",
            "file": workflow.file_name,
            "description": workflow.description,
            "legacy": bool(workflow.superseded_by),
            "superseded_by": workflow.superseded_by,
            "inputs": len(workflow.inputs),
            "secrets": len(workflow.secrets),
            "outputs": len(workflow.outputs),
        }

    def _action_entry(self, action: CompositeAction) -> dict[str, Any]:
        """Return the data entry for one composite action.

        Args:
            action: The action to describe.

        Returns:
            A mapping ready for YAML serialization.
        """
        return {
            "title": action.title,
            "slug": action.slug,
            "url": f"reference/actions/{action.slug}.html",
            "description": action.description,
            "inputs": len(action.inputs),
            "outputs": len(action.outputs),
        }

    def _write_text(self, path: Path, content: str) -> None:
        """Write text to a file, creating parent directories as needed.

        Args:
            path: Destination file.
            content: Text to write.
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def main() -> None:
    """Generate the documentation from the repository in which this script lives."""
    DocsGenerator(REPO_ROOT, SpecParser(), MarkdownRenderer()).run()


if __name__ == "__main__":
    main()
