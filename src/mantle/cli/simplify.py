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
    """Print per-category and aggregate diff stats as key=value lines.

    Args:
        issue: Issue number to collect diff stats for.
        project_dir: Project directory. Defaults to cwd.
    """
    if project_dir is None:
        project_dir = Path.cwd()

    categories = simplify.collect_issue_diff_stats_categorised(
        project_dir, issue
    )

    # Legacy aggregate lines — sum of primary categories only.
    aggregate_files = aggregate_added = aggregate_removed = 0
    for name in simplify.PRIMARY_CATEGORIES:
        stats = categories.get(name)
        if stats is None:
            continue
        aggregate_files += stats.files
        aggregate_added += stats.lines_added
        aggregate_removed += stats.lines_removed
    console.print(f"files={aggregate_files}")
    console.print(f"lines_added={aggregate_added}")
    console.print(f"lines_removed={aggregate_removed}")
    console.print(f"lines_changed={aggregate_added + aggregate_removed}")

    # Per-category breakdown, in declaration order.
    for name, stats in categories.items():
        console.print(f"{name}_files={stats.files}")
        console.print(f"{name}_lines_added={stats.lines_added}")
        console.print(f"{name}_lines_removed={stats.lines_removed}")
        console.print(f"{name}_lines_changed={stats.lines_changed}")


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
