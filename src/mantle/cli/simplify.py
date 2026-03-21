"""CLI wrappers for simplification operations."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from mantle.core import simplify

console = Console()


def run_collect_issue_files(
    *,
    issue: int,
    project_dir: Path | None = None,
) -> None:
    """Collect and print files changed by an issue.

    Args:
        issue: Issue number to collect files for.
        project_dir: Project directory. Defaults to cwd.
    """
    if project_dir is None:
        project_dir = Path.cwd()

    try:
        files = simplify.collect_issue_files(project_dir, issue)
    except simplify.NoCommitsFoundError:
        console.print(f"[red]Error:[/red] No commits found for issue {issue}.")
        raise SystemExit(1) from None

    for f in files:
        console.print(f)


def run_collect_changed_files(
    *,
    project_dir: Path | None = None,
) -> None:
    """Collect and print all changed files in the working tree.

    Args:
        project_dir: Project directory. Defaults to cwd.
    """
    if project_dir is None:
        project_dir = Path.cwd()

    files = simplify.collect_changed_files(project_dir)
    for f in files:
        console.print(f)
