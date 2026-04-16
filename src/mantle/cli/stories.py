"""CLI wrapper for story planning operations."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from mantle.cli import errors
from mantle.core import stories

console = Console()


def run_save_story(
    *,
    issue: int,
    title: str,
    content: str,
    story: int | None = None,
    overwrite: bool = False,
    project_dir: Path | None = None,
) -> None:
    """Save story, print confirmation, suggest next step.

    Args:
        issue: Parent issue number.
        title: Short title for the story.
        content: Full story body (markdown).
        story: Explicit story number (for overwrites).
        overwrite: Replace existing story file.
        project_dir: Project directory. Defaults to cwd.

    Raises:
        SystemExit: If story already exists.
    """
    if project_dir is None:
        project_dir = Path.cwd()

    try:
        note, path = stories.save_story(
            project_dir,
            content,
            issue=issue,
            title=title,
            story=story,
            overwrite=overwrite,
        )
    except stories.StoryExistsError:
        console.print(
            "[yellow]Warning:[/yellow] Story already"
            " exists. Use --overwrite to replace."
        )
        raise SystemExit(1) from None

    story_count = stories.count_stories(project_dir, issue=issue)

    console.print()
    console.print(f"[green]Saved {path.name} to .mantle/stories/[/green]")
    console.print(f"  Issue: {note.issue}")
    console.print(f"  Title: {note.title}")
    console.print(f"  Stories for issue {note.issue}: {story_count}")
    console.print(
        "  Next: run [bold]/mantle:plan-stories[/bold] for more"
        " or [bold]/mantle:implement[/bold] to start building"
    )


def run_update_story_status(
    *,
    issue: int,
    story: int,
    status: str,
    failure_log: str | None = None,
    project_dir: Path | None = None,
) -> None:
    """Update a story's status on disk.

    Args:
        issue: Parent issue number.
        story: Story number within the issue.
        status: New status value (planned, in-progress,
            completed, blocked).
        failure_log: Error details when marking blocked.
        project_dir: Project directory. Defaults to cwd.

    Raises:
        SystemExit: If the story file is not found.
    """
    if project_dir is None:
        project_dir = Path.cwd()

    try:
        stories.update_story_status(
            project_dir,
            issue=issue,
            story=story,
            status=status,
            failure_log=failure_log,
        )
    except FileNotFoundError:
        errors.exit_with_error(
            f"Story {story} for issue {issue} not found.",
            hint=(
                f"Check the story ID with 'mantle list-stories --issue {issue}'"
            ),
        )

    console.print()
    console.print(
        f"[green]Updated story {story} (issue {issue}):[/green] {status}"
    )
