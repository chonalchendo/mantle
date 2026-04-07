"""Save-brainstorm command — persist a brainstorm session."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from mantle.core import brainstorm

console = Console()

_NEXT_STEPS: dict[str, str] = {
    "proceed": (
        "  Next: run [bold]/mantle:add-issue[/bold] to create the issue"
    ),
    "research": (
        "  Next: run [bold]/mantle:research[/bold] to gather evidence"
    ),
    "scrap": ("  Idea scrapped — focus on existing backlog"),
}


def run_save_brainstorm(
    *,
    title: str,
    verdict: str,
    content: str,
    project_dir: Path | None = None,
) -> None:
    """Save brainstorm session, print confirmation, suggest next step.

    Args:
        title: Short title for the brainstormed idea.
        verdict: Outcome verdict (proceed, research, or scrap).
        content: Full brainstorm session content.
        project_dir: Project directory. Defaults to cwd.

    Raises:
        SystemExit: If verdict is invalid.
    """
    if project_dir is None:
        project_dir = Path.cwd()

    try:
        note, path = brainstorm.save_brainstorm(
            project_dir,
            content,
            title=title,
            verdict=verdict,
        )
    except ValueError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise SystemExit(1) from None

    console.print()
    console.print(f"[green]Brainstorm saved to {path.name}[/green]")
    console.print()
    console.print(f"  Date:    {note.date}")
    console.print(f"  Author:  {note.author}")
    console.print(f"  Title:   {note.title}")
    console.print(f"  Verdict: {note.verdict}")
    console.print()
    console.print(_NEXT_STEPS[note.verdict])
