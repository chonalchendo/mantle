"""CLI wrappers for issue planning operations."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from mantle.core import issues, state

console = Console()


def run_save_issue(
    *,
    title: str,
    slice: tuple[str, ...],
    content: str,
    blocked_by: tuple[int, ...] = (),
    skills_required: tuple[str, ...] = (),
    verification: str | None = None,
    issue: int | None = None,
    overwrite: bool = False,
    project_dir: Path | None = None,
) -> None:
    """Save issue, print confirmation, suggest next step.

    Args:
        title: Short title for the issue.
        slice: Architectural layers this issue touches.
        content: Full issue body (markdown).
        blocked_by: Issue numbers this issue depends on.
        skills_required: Skill names required to work on this issue.
        verification: Optional per-issue verification override.
        issue: Explicit issue number (for overwrites).
        overwrite: Replace existing issue file.
        project_dir: Project directory. Defaults to cwd.

    Raises:
        SystemExit: If issue already exists or transition is invalid.
    """
    if project_dir is None:
        project_dir = Path.cwd()

    try:
        note, path = issues.save_issue(
            project_dir,
            content,
            title=title,
            slice=slice,
            blocked_by=blocked_by,
            skills_required=skills_required,
            verification=verification,
            issue=issue,
            overwrite=overwrite,
        )
    except issues.IssueExistsError:
        console.print(
            "[yellow]Warning:[/yellow] Issue already"
            " exists. Use --overwrite to replace."
        )
        raise SystemExit(1) from None
    except state.InvalidTransitionError as exc:
        console.print(
            f"[red]Error:[/red] Cannot plan issues from"
            f" '{exc.current.value}' status."
        )
        if exc.valid_targets:
            targets = ", ".join(sorted(s.value for s in exc.valid_targets))
            console.print(f"  Valid next steps: {targets}")
        raise SystemExit(1) from None

    console.print()
    console.print(f"[green]Saved {path.name} to .mantle/issues/[/green]")
    console.print(f"  Title: {note.title}")
    console.print(f"  Slice: {', '.join(note.slice)}")
    if note.blocked_by:
        refs = ", ".join(f"issue-{n:02d}" for n in note.blocked_by)
        console.print(f"  Blocked by: {refs}")
    console.print(
        "  Next: run [bold]/mantle:build[/bold] to automate the full"
        " pipeline, [bold]/mantle:shape-issue[/bold] for manual control,"
        " or [bold]/mantle:plan-issues[/bold] for the next issue"
    )


def run_set_slices(
    *,
    slices: tuple[str, ...],
    project_dir: Path | None = None,
) -> None:
    """Set project architectural slices, print confirmation.

    Args:
        slices: Architectural layer names.
        project_dir: Project directory. Defaults to cwd.
    """
    if project_dir is None:
        project_dir = Path.cwd()

    state.update_slices(project_dir, slices)

    console.print()
    console.print(f"[green]Project slices defined ({len(slices)}):[/green]")
    console.print(f"  {', '.join(slices)}")
