"""Save-research command — persist a research note."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from mantle.core import research

console = Console()


def run_save_research(
    *,
    focus: str,
    confidence: str,
    content: str,
    project_dir: Path | None = None,
) -> None:
    """Save research note, print confirmation, suggest next steps.

    Args:
        focus: Research focus angle.
        confidence: Confidence rating (e.g. "7/10").
        content: Research note body content.
        project_dir: Project directory. Defaults to cwd.

    Raises:
        SystemExit: If idea.md does not exist or args are invalid.
    """
    if project_dir is None:
        project_dir = Path.cwd()

    try:
        note, path = research.save_research(
            project_dir, content, focus=focus, confidence=confidence
        )
    except research.IdeaNotFoundError:
        console.print(
            "[yellow]Warning:[/yellow] No idea.md found. "
            "Run /mantle:idea first."
        )
        raise SystemExit(1) from None
    except ValueError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise SystemExit(1) from None

    console.print()
    console.print(f"[green]Research saved to {path.name}[/green]")
    console.print()
    console.print(f"  Date:       {note.date}")
    console.print(f"  Author:     {note.author}")
    console.print(f"  Focus:      {note.focus}")
    console.print(f"  Confidence: {note.confidence}")
    console.print()
    console.print("  Next: run [bold]/mantle:research[/bold] for another angle")
    console.print(
        "        or [bold]/mantle:design-product[/bold] to define the product"
    )
