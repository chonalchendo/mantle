"""Save-learning command — persist an implementation learning."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from mantle.cli import errors
from mantle.core import learning

console = Console()


def run_save_learning(
    *,
    issue: int,
    title: str,
    confidence_delta: str,
    content: str,
    overwrite: bool = False,
    project_dir: Path | None = None,
) -> None:
    """Save learning, print confirmation, suggest next step.

    Args:
        issue: Issue number this learning relates to.
        title: Short title for the learning.
        confidence_delta: Confidence change (e.g. "+2", "-1").
        content: Structured reflection body.
        overwrite: Replace existing learning file.
        project_dir: Project directory. Defaults to cwd.

    Raises:
        SystemExit: If learning exists, the target issue is not
            found, or validation fails.
    """
    if project_dir is None:
        project_dir = Path.cwd()

    try:
        note, path = learning.save_learning(
            project_dir,
            content,
            issue=issue,
            title=title,
            confidence_delta=confidence_delta,
            overwrite=overwrite,
        )
    except learning.LearningExistsError:
        console.print(
            "[yellow]Warning:[/yellow] Learning already"
            " exists. Use --overwrite to replace."
        )
        raise SystemExit(1) from None
    except learning.IssueNotFoundError as exc:
        errors.exit_with_error(
            (
                f"{exc}. If the issue is archived, save the learning"
                " before running /mantle:archive, or edit the archived"
                " issue file directly."
            ),
            hint=(
                "See the error above; file a bug at"
                " https://github.com/chonalchendo/mantle/issues"
                " if unexpected"
            ),
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
    console.print(f"[green]Learning saved to {path.name}[/green]")
    console.print()
    console.print(f"  Issue:            {note.issue}")
    console.print(f"  Title:            {note.title}")
    console.print(f"  Confidence delta: {note.confidence_delta}")
    console.print(f"  Author:           {note.author}")
    console.print()
    console.print(
        "  Learnings auto-surface in future"
        " [bold]/mantle:build[/bold] and"
        " [bold]/mantle:shape-issue[/bold] sessions"
    )
