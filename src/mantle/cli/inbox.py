"""CLI wrappers for inbox capture operations."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from mantle.cli import errors
from mantle.core import inbox

console = Console()


def run_save_inbox_item(
    *,
    title: str,
    description: str = "",
    source: str = "user",
    project_dir: Path | None = None,
) -> None:
    """Save an inbox item to .mantle/inbox/.

    Args:
        title: One-line item title.
        description: Optional free-text description (body).
        source: Origin of the item (user or ai).
        project_dir: Project directory. Defaults to cwd.

    Raises:
        SystemExit: On invalid source.
    """
    if project_dir is None:
        project_dir = Path.cwd()

    try:
        item, path = inbox.save_inbox_item(
            project_dir,
            title=title,
            description=description,
            source=source,
        )
    except ValueError as exc:
        errors.exit_with_error(
            str(exc),
            hint=errors.UNEXPECTED_BUG_HINT,
        )

    console.print()
    console.print("[green]Inbox item saved to .mantle/inbox/[/green]")
    console.print(f"  Title: {item.title}")
    console.print(f"  Source: {item.source}")
    console.print(f"  File: {path.name}")


def run_update_inbox_status(
    *,
    item: str,
    status: str,
    project_dir: Path | None = None,
) -> None:
    """Update an inbox item's status.

    Args:
        item: Item filename (e.g. 2026-04-05-slug.md).
        status: New status (open, promoted, dismissed).
        project_dir: Project directory. Defaults to cwd.

    Raises:
        SystemExit: On missing item or invalid status.
    """
    if project_dir is None:
        project_dir = Path.cwd()

    try:
        updated, old_status = inbox.update_inbox_status(
            project_dir,
            item,
            status=status,
        )
    except FileNotFoundError:
        errors.exit_with_error(
            f"Inbox item not found: {item}",
            hint="List inbox items with 'mantle list-inbox'",
        )
    except ValueError as exc:
        errors.exit_with_error(
            str(exc),
            hint=errors.UNEXPECTED_BUG_HINT,
        )

    console.print()
    console.print(f"[green]Item updated:[/green] {item}")
    console.print(f"  Status: {old_status} \u2192 {updated.status}")
