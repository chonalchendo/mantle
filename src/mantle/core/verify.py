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
    issue_path = (
        project_root / ".mantle" / "issues" / f"issue-{issue_number:02d}.md"
    )
    if issue_path.exists():
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
