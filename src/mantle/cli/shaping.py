"""Save-shaped-issue command — persist a shaped issue artifact."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from mantle.core import shaping

console = Console()


def run_save_shaped_issue(
    *,
    issue: int,
    title: str,
    approaches: tuple[str, ...],
    chosen_approach: str,
    appetite: str,
    content: str,
    open_questions: tuple[str, ...] = (),
    overwrite: bool = False,
    project_dir: Path | None = None,
) -> None:
    """Save shaped issue, print confirmation, suggest next step.

    Args:
        issue: Issue number being shaped.
        title: Short title for the shaped issue.
        approaches: Approaches that were evaluated.
        chosen_approach: The selected approach name.
        appetite: Time/effort budget.
        content: Full shaping write-up body.
        open_questions: Unresolved questions, if any.
        overwrite: Replace existing shaped issue file.
        project_dir: Project directory. Defaults to cwd.

    Raises:
        SystemExit: If shaped issue already exists.
    """
    if project_dir is None:
        project_dir = Path.cwd()

    try:
        note, path = shaping.save_shaped_issue(
            project_dir,
            content,
            issue=issue,
            title=title,
            approaches=approaches,
            chosen_approach=chosen_approach,
            appetite=appetite,
            open_questions=open_questions,
            overwrite=overwrite,
        )
    except shaping.ShapedIssueExistsError:
        console.print(
            "[yellow]Warning:[/yellow] Shaped issue already"
            " exists. Use --overwrite to replace."
        )
        raise SystemExit(1) from None

    console.print()
    console.print(f"[green]Shaped issue saved to {path.name}[/green]")
    console.print()
    console.print(f"  Issue:    {note.issue}")
    console.print(f"  Title:    {note.title}")
    console.print(f"  Approach: {note.chosen_approach}")
    console.print(f"  Appetite: {note.appetite}")
    console.print(f"  Author:   {note.author}")
    console.print()
    console.print(
        "  Next: run [bold]/mantle:plan-stories[/bold]"
        " to decompose into stories"
    )
