"""Save-scout command — persist a scout report."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from mantle.cli import errors
from mantle.core import scout

console = Console()


def run_save_scout(
    *,
    repo_url: str,
    repo_name: str,
    dimensions: list[str],
    content: str,
    project_dir: Path | None = None,
) -> None:
    """Save scout report, print confirmation, suggest next step.

    Args:
        repo_url: Full URL of the scouted repository.
        repo_name: Short name of the scouted repository.
        dimensions: Analysis dimensions covered in the report.
        content: Full scout report content.
        project_dir: Project directory. Defaults to cwd.

    Raises:
        SystemExit: If saving fails with a ValueError.
    """
    if project_dir is None:
        project_dir = Path.cwd()

    try:
        note, path = scout.save_scout(
            project_dir,
            content,
            repo_url=repo_url,
            repo_name=repo_name,
            dimensions=tuple(dimensions),
        )
    except ValueError as exc:
        errors.exit_with_error(
            str(exc),
            hint=errors.UNEXPECTED_BUG_HINT,
        )

    console.print()
    console.print(f"[green]Scout report saved to {path.name}[/green]")
    console.print()
    console.print(f"  Repo:       {note.repo_name}")
    console.print(f"  Date:       {note.date}")
    console.print(f"  Author:     {note.author}")
    console.print(f"  Dimensions: {len(note.dimensions)} covered")
    console.print()
    console.print(
        "  Next: run [bold]/mantle:query[/bold] to search scout findings"
    )
