"""Save-challenge command — persist a challenge session transcript."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from mantle.core import challenge

console = Console()


def run_save_challenge(
    *,
    transcript: str,
    project_dir: Path | None = None,
) -> None:
    """Save transcript, print confirmation, suggest next step.

    Args:
        transcript: Full challenge session transcript.
        project_dir: Project directory. Defaults to cwd.

    Raises:
        SystemExit: If idea.md does not exist.
    """
    if project_dir is None:
        project_dir = Path.cwd()

    try:
        note, path = challenge.save_challenge(project_dir, transcript)
    except challenge.IdeaNotFoundError:
        console.print(
            "[yellow]Warning:[/yellow] No idea.md found. "
            "Run /mantle:idea first."
        )
        raise SystemExit(1) from None

    console.print()
    console.print(
        f"[green]Challenge saved to {path.name}[/green]"
    )
    console.print()
    console.print(f"  Date:   {note.date}")
    console.print(f"  Author: {note.author}")
    console.print()
    console.print(
        "  Next: run [bold]/mantle:design-product[/bold] "
        "to define the product"
    )
