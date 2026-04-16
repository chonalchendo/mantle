"""Save-research command — persist a research note."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from mantle.cli import errors
from mantle.core import research

console = Console()


def run_save_research(
    *,
    focus: str,
    confidence: str,
    content: str,
    update_state: bool = True,
    project_dir: Path | None = None,
    issue: int | None = None,
) -> None:
    """Save research note, print confirmation, suggest next steps.

    Args:
        focus: Research focus angle.
        confidence: Confidence rating (e.g. "7/10").
        content: Research note body content.
        update_state: Whether to update state.md. False when
            research is a sub-step of another command.
        project_dir: Project directory. Defaults to cwd.
        issue: Save in issue mode for this issue number.

    Raises:
        SystemExit: If prerequisites are missing or args are invalid.
    """
    if project_dir is None:
        project_dir = Path.cwd()

    try:
        note, path = research.save_research(
            project_dir,
            content,
            focus=focus,
            confidence=confidence,
            update_state=update_state,
            issue=issue,
        )
    except research.IdeaNotFoundError:
        console.print(
            "[yellow]Warning:[/yellow] No idea.md found. "
            "Run /mantle:idea first, or pass --issue to save issue-mode "
            "research."
        )
        raise SystemExit(1) from None
    except research.IssueNotFoundError as exc:
        errors.exit_with_error(
            f"No issue file found for issue {exc.issue}.",
            hint="Check the issue number with 'mantle list-issues'",
        )
    except ValueError as exc:
        errors.exit_with_error(
            str(exc),
            hint=(
                "See the error above; file a bug at"
                " https://github.com/chonalchendo/mantle/issues"
                " if unexpected"
            ),
        )

    console.print()
    console.print(f"[green]Research saved to {path.name}[/green]")
    console.print()
    console.print(f"  Date:       {note.date}")
    console.print(f"  Author:     {note.author}")
    console.print(f"  Focus:      {note.focus}")
    console.print(f"  Confidence: {note.confidence}")
    if issue is not None:
        console.print(f"  Issue:      {issue}")
    console.print()
    if issue is not None:
        console.print(
            "  Next: run [bold]/mantle:shape-issue[/bold] "
            "to fold the research into a chosen approach"
        )
    else:
        console.print(
            "  Next: run [bold]/mantle:research[/bold] for another angle"
        )
        console.print(
            "        or [bold]/mantle:design-product[/bold] "
            "to define the product"
        )
