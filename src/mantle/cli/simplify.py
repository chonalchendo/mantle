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

    files = simplify.collect_issue_files(project_dir, issue)

    if not files:
        console.print(f"No commits found for issue {issue}.")
        return

    for f in files:
        console.print(f)
    console.print(f"{len(files)} file(s) changed.")


def run_collect_issue_diff_stats(
    *,
    issue: int,
    project_dir: Path | None = None,
) -> None:
    """Print diff stats for an issue as key=value lines.

    Args:
        issue: Issue number to collect diff stats for.
        project_dir: Project directory. Defaults to cwd.
    """
    if project_dir is None:
        project_dir = Path.cwd()

    stats = simplify.collect_issue_diff_stats(project_dir, issue)
    console.print(f"files={stats.files}")
    console.print(f"lines_added={stats.lines_added}")
    console.print(f"lines_removed={stats.lines_removed}")
    console.print(f"lines_changed={stats.lines_changed}")


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
