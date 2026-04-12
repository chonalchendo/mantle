"""Show-patterns command — surface recurring themes from learnings."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from mantle.core import patterns

console = Console()


def run_show_patterns(*, project_dir: Path | None = None) -> None:
    """Analyze vault patterns and print the markdown report.

    Args:
        project_dir: Project directory. Defaults to cwd.
    """
    if project_dir is None:
        project_dir = Path.cwd()

    report = patterns.analyze_patterns(project_dir)
    console.print(patterns.render_report(report))
