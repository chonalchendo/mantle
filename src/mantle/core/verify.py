"""Verification — strategy loading, report building."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pydantic

from mantle.core import issues, project

if TYPE_CHECKING:
    from pathlib import Path


# ── Data model ───────────────────────────────────────────────────


class VerificationResult(pydantic.BaseModel, frozen=True):
    """Single verification criterion result.

    Attributes:
        criterion: Description of what was checked.
        passed: Whether the criterion passed.
        detail: Optional detail about the result.
    """

    criterion: str
    passed: bool
    detail: str | None = None


class VerificationReport(pydantic.BaseModel, frozen=True):
    """Full verification report for an issue.

    Attributes:
        issue: Issue number that was verified.
        title: Issue title.
        results: Tuple of individual criterion results.
        strategy_used: The verification strategy text.
        is_override: Whether a per-issue override was used.
    """

    issue: int
    title: str
    results: tuple[VerificationResult, ...]
    strategy_used: str
    is_override: bool

    @property
    def passed(self) -> bool:
        """True if all criteria passed."""
        return all(r.passed for r in self.results)


# ── Exception ────────────────────────────────────────────────────


class VerificationStrategyNotFoundError(Exception):
    """Raised when no verification strategy is found.

    Neither the project config nor the issue has a strategy.
    """

    def __init__(self, issue_number: int) -> None:
        self.issue_number = issue_number
        super().__init__(
            f"No verification strategy found for issue {issue_number}"
        )


# ── Public API ───────────────────────────────────────────────────


def load_strategy(project_root: Path, issue_number: int) -> tuple[str, bool]:
    """Load verification strategy for an issue.

    Checks the issue file for a per-issue ``verification`` override
    first. Falls back to the project-wide strategy in config.md.

    Args:
        project_root: Directory containing .mantle/.
        issue_number: Issue number to load strategy for.

    Returns:
        Tuple of (strategy text, is_override). ``is_override`` is
        True when the strategy came from the issue file.

    Raises:
        VerificationStrategyNotFoundError: If no strategy exists
            in either the issue or the project config.
    """
    issue_path = issues.find_issue_path(project_root, issue_number)
    if issue_path is not None:
        note, _ = issues.load_issue(issue_path)
        if note.verification:
            return note.verification, True

    config = project.read_config(project_root)
    strategy = config.get("verification_strategy")
    if strategy:
        return strategy, False

    raise VerificationStrategyNotFoundError(issue_number)


def save_strategy(project_root: Path, strategy: str) -> None:
    """Persist verification strategy to config.md.

    Args:
        project_root: Directory containing .mantle/.
        strategy: Verification strategy text to save.
    """
    project.update_config(project_root, verification_strategy=strategy)


def introspect_project(
    project_root: Path,
) -> dict[str, str | None]:
    """Auto-detect test/lint/check commands from project files.

    Reads CLAUDE.md, pyproject.toml, Justfile, and Makefile to
    detect common development commands via simple string matching.

    Args:
        project_root: Root directory of the project.

    Returns:
        Dict with keys ``test_command``, ``lint_command``,
        ``check_command``, ``type_check_command``. Values are
        detected command strings or None.
    """
    result: dict[str, str | None] = {
        "test_command": None,
        "lint_command": None,
        "check_command": None,
        "type_check_command": None,
    }

    _introspect_claude_md(project_root, result)
    _introspect_pyproject(project_root, result)
    _introspect_justfile(project_root, result)
    _introspect_makefile(project_root, result)

    return result


def generate_structured_strategy(
    introspection: dict[str, str | None],
) -> str:
    """Build a markdown verification strategy from introspection.

    Takes the dict produced by ``introspect_project`` and renders
    a human-readable markdown strategy with labelled sections.

    Args:
        introspection: Dict with ``test_command``,
            ``lint_command``, ``check_command``, and
            ``type_check_command`` keys.

    Returns:
        Multiline markdown string.
    """
    test_cmd = introspection.get("test_command")
    lint_cmd = introspection.get("lint_command")
    check_cmd = introspection.get("check_command")
    type_cmd = introspection.get("type_check_command")

    sections: list[str] = []

    # Test Command
    test_value = test_cmd or "Not detected — configure manually"
    if check_cmd and not test_cmd:
        test_value = (
            f"Not detected — configure manually "
            f"(covered by `{check_cmd}`?)"
        )
    elif check_cmd and test_cmd:
        test_value = (
            f"{test_cmd} (also covered by `{check_cmd}`)"
        )
    sections.append(f"## Test Command\n{test_value}")

    # Lint/Format Check
    lint_value = lint_cmd or "Not detected"
    if check_cmd and not lint_cmd:
        lint_value = (
            f"Not detected (covered by `{check_cmd}`?)"
        )
    elif check_cmd and lint_cmd:
        lint_value = (
            f"{lint_cmd} (also covered by `{check_cmd}`)"
        )
    sections.append(f"## Lint/Format Check\n{lint_value}")

    # Type Check
    type_value = type_cmd or "Not detected"
    if check_cmd and not type_cmd:
        type_value = (
            f"Not detected (covered by `{check_cmd}`?)"
        )
    elif check_cmd and type_cmd:
        type_value = (
            f"{type_cmd} (also covered by `{check_cmd}`)"
        )
    sections.append(f"## Type Check\n{type_value}")

    # Acceptance Criteria Verification
    sections.append(
        "## Acceptance Criteria Verification\n"
        "Run the test suite, then verify each acceptance "
        "criterion independently by reading implementation "
        "code, checking file existence, and confirming "
        "behaviour matches the specification."
    )

    return "\n\n".join(sections) + "\n"


# ── Private helpers ─────────────────────────────────────────────


def _read_file_text(path: Path) -> str | None:
    """Read a file as UTF-8 text, returning None if missing."""
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None


def _extract_backtick_command(line: str) -> str | None:
    """Extract a command from backticks in a line.

    Returns the text between the first pair of backticks, or
    None if no backticks are found.
    """
    start = line.find("`")
    if start == -1:
        return None
    end = line.find("`", start + 1)
    if end == -1:
        return None
    return line[start + 1 : end]


def _introspect_claude_md(
    project_root: Path,
    result: dict[str, str | None],
) -> None:
    """Scan CLAUDE.md for test/lint/check commands."""
    text = _read_file_text(project_root / "CLAUDE.md")
    if text is None:
        return

    for line in text.splitlines():
        lower = line.lower()
        cmd = _extract_backtick_command(line)
        if cmd is None:
            continue

        if (
            "run tests" in lower
            or ("test" in lower and "pytest" in lower)
        ) and result["test_command"] is None:
            result["test_command"] = cmd

        if (
            "run all checks" in lower or "check" in lower
        ) and "test" not in lower and (
            result["check_command"] is None
        ):
            result["check_command"] = cmd

        if (
            "lint" in lower
            or "format" in lower
            or "fix" in lower
        ) and result["lint_command"] is None and (
            "ruff" in cmd or "lint" in lower
        ):
            result["lint_command"] = cmd

        if (
            ("type" in lower and "check" in lower)
            or "mypy" in lower
            or "pyright" in lower
        ) and result["type_check_command"] is None:
            result["type_check_command"] = cmd


def _introspect_pyproject(
    project_root: Path,
    result: dict[str, str | None],
) -> None:
    """Scan pyproject.toml for tool configuration."""
    text = _read_file_text(project_root / "pyproject.toml")
    if text is None:
        return

    if "[tool.pytest" in text and result["test_command"] is None:
        result["test_command"] = "pytest"

    if "[tool.ruff" in text and result["lint_command"] is None:
        result["lint_command"] = "ruff check ."

    if (
        "[tool.mypy" in text
        and result["type_check_command"] is None
    ):
        result["type_check_command"] = "mypy"


def _introspect_justfile(
    project_root: Path,
    result: dict[str, str | None],
) -> None:
    """Scan Justfile for common recipe names."""
    text = _read_file_text(project_root / "Justfile")
    if text is None:
        return

    lines = text.splitlines()
    for i, line in enumerate(lines):
        stripped = line.strip()

        if (
            stripped.startswith("test")
            and ":" in stripped
            and result["test_command"] is None
        ):
            # Use the recipe body if available.
            if i + 1 < len(lines) and lines[
                i + 1
            ].startswith("    "):
                result["test_command"] = (
                    lines[i + 1].strip()
                )
            else:
                result["test_command"] = "just test"

        if (
            stripped.startswith("check")
            and ":" in stripped
            and result["check_command"] is None
        ):
            result["check_command"] = "just check"

        if (
            stripped.startswith("lint")
            and ":" in stripped
            and result["lint_command"] is None
        ):
            result["lint_command"] = "just lint"

        if (
            stripped.startswith("fix")
            and ":" in stripped
            and result["lint_command"] is None
        ):
            result["lint_command"] = "just fix"


def _introspect_makefile(
    project_root: Path,
    result: dict[str, str | None],
) -> None:
    """Scan Makefile for common target names."""
    text = _read_file_text(project_root / "Makefile")
    if text is None:
        return

    for line in text.splitlines():
        stripped = line.strip()

        if (
            stripped.startswith("test")
            and ":" in stripped
            and result["test_command"] is None
        ):
            result["test_command"] = "make test"

        if (
            stripped.startswith("check")
            and ":" in stripped
            and result["check_command"] is None
        ):
            result["check_command"] = "make check"

        if (
            stripped.startswith("lint")
            and ":" in stripped
            and result["lint_command"] is None
        ):
            result["lint_command"] = "make lint"


def build_report(
    issue_number: int,
    title: str,
    results: list[tuple[str, bool, str | None]],
    strategy_used: str,
    is_override: bool,
) -> VerificationReport:
    """Construct a VerificationReport from raw result tuples.

    Args:
        issue_number: Issue number that was verified.
        title: Issue title.
        results: List of (criterion, passed, detail) tuples.
        strategy_used: The verification strategy text used.
        is_override: Whether a per-issue override was used.

    Returns:
        A VerificationReport instance.
    """
    verification_results = tuple(
        VerificationResult(criterion=criterion, passed=passed, detail=detail)
        for criterion, passed, detail in results
    )
    return VerificationReport(
        issue=issue_number,
        title=title,
        results=verification_results,
        strategy_used=strategy_used,
        is_override=is_override,
    )


def format_report(report: VerificationReport) -> str:
    """Render a verification report as markdown.

    Args:
        report: The verification report to format.

    Returns:
        Markdown string with checkmarks/crosses per criterion.
    """
    status = "PASSED" if report.passed else "FAILED"
    lines = [
        f"# Verification Report — Issue {report.issue}",
        "",
        f"**{report.title}**",
        "",
        f"**Status:** {status}",
        f"**Strategy:** {'per-issue override' if report.is_override else 'project default'}",
        "",
        "## Results",
        "",
    ]
    for r in report.results:
        mark = "\u2713" if r.passed else "\u2717"
        line = f"- {mark} {r.criterion}"
        if r.detail:
            line += f" — {r.detail}"
        lines.append(line)

    lines.append("")
    return "\n".join(lines)
