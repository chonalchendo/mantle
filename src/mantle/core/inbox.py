"""Inbox capture — structured inbox items for feature ideas."""

from __future__ import annotations

import re
from datetime import date
from typing import TYPE_CHECKING

import pydantic

from mantle.core import state, vault

if TYPE_CHECKING:
    from pathlib import Path


# ── Constants ───────────────────────────────────────────────────

VALID_SOURCES: frozenset[str] = frozenset({"user", "ai"})
VALID_STATUSES: frozenset[str] = frozenset(
    {"open", "promoted", "dismissed"}
)


# ── Data model ──────────────────────────────────────────────────


class InboxItem(pydantic.BaseModel, frozen=True):
    """Inbox item frontmatter schema.

    Attributes:
        date: Date the item was captured.
        author: Git email of the item author.
        title: One-line item title.
        source: Origin of the item (user or ai).
        status: Item lifecycle status (open, promoted, dismissed).
        tags: Mantle tags for categorization.
    """

    date: date
    author: str
    title: str
    source: str = "user"
    status: str = "open"
    tags: tuple[str, ...] = ("type/inbox", "status/open")


# ── Public API ──────────────────────────────────────────────────


def save_inbox_item(
    project_dir: Path,
    *,
    title: str,
    description: str = "",
    source: str = "user",
) -> tuple[InboxItem, Path]:
    """Save an inbox item to .mantle/inbox/<date>-<slug>.md.

    Auto-increments filename on same-day collision.

    Args:
        project_dir: Directory containing .mantle/.
        title: One-line item title.
        description: Optional free-text description (body).
        source: Origin of the item (user or ai).

    Returns:
        Tuple of (InboxItem frontmatter, path to saved file).

    Raises:
        ValueError: If source is not valid.
    """
    _validate_choice(source, VALID_SOURCES, "source")

    identity = state.resolve_git_identity()
    today = date.today()
    slug = _slugify(title)
    item_path = _resolve_inbox_path(project_dir, str(today), slug)

    item = InboxItem(
        date=today,
        author=identity,
        title=title,
        source=source,
    )

    vault.write_note(item_path, item, description)

    return item, item_path


def load_inbox_item(path: Path) -> tuple[InboxItem, str]:
    """Read an inbox item by absolute path.

    Args:
        path: Absolute path to the inbox item file.

    Returns:
        Tuple of (InboxItem frontmatter, body text).

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    note = vault.read_note(path, InboxItem)
    return note.frontmatter, note.body


def list_inbox_items(
    project_dir: Path,
    *,
    status: str | None = None,
) -> list[Path]:
    """All inbox item paths in .mantle/inbox/, sorted oldest-first.

    Args:
        project_dir: Directory containing .mantle/.
        status: Filter to items matching this status (optional).

    Returns:
        List of paths to inbox item files. Empty if none.
    """
    inbox_dir = project_dir / ".mantle" / "inbox"
    if not inbox_dir.is_dir():
        return []

    paths = sorted(inbox_dir.glob("*.md"))

    if status is None:
        return paths

    return [
        path for path in paths
        if load_inbox_item(path)[0].status == status
    ]


def update_inbox_status(
    project_dir: Path,
    item_filename: str,
    *,
    status: str,
) -> tuple[InboxItem, str]:
    """Update an inbox item's status.

    Args:
        project_dir: Directory containing .mantle/.
        item_filename: Item filename (e.g. "2026-04-05-slug.md").
        status: New status (open, promoted, dismissed).

    Returns:
        Tuple of (updated InboxItem, previous status string).

    Raises:
        FileNotFoundError: If the item file does not exist.
        ValueError: If the status is not valid.
    """
    _validate_choice(status, VALID_STATUSES, "status")

    item_path = project_dir / ".mantle" / "inbox" / item_filename

    try:
        note = vault.read_note(item_path, InboxItem)
    except FileNotFoundError:
        msg = f"Inbox item not found: {item_path}"
        raise FileNotFoundError(msg) from None

    current = note.frontmatter

    old_status_tag = f"status/{current.status}"
    new_status_tag = f"status/{status}"
    tags = tuple(
        new_status_tag if t == old_status_tag else t
        for t in current.tags
    )

    old_status = current.status
    updated = current.model_copy(
        update={"status": status, "tags": tags},
    )
    vault.write_note(item_path, updated, note.body)

    return updated, old_status


# ── Internal helpers ────────────────────────────────────────────


def _resolve_inbox_path(
    project_dir: Path,
    date_str: str,
    slug: str,
) -> Path:
    """Compute non-colliding inbox item path with auto-increment.

    Args:
        project_dir: Directory containing .mantle/.
        date_str: Date string (YYYY-MM-DD).
        slug: Slugified title.

    Returns:
        Path for the new inbox item file.
    """
    inbox_dir = project_dir / ".mantle" / "inbox"
    base = inbox_dir / f"{date_str}-{slug}.md"
    if not base.exists():
        return base

    counter = 2
    while True:
        path = inbox_dir / f"{date_str}-{slug}-{counter}.md"
        if not path.exists():
            return path
        counter += 1


def _slugify(title: str) -> str:
    """Convert title to a filename-safe slug (max 30 chars).

    Args:
        title: The inbox item title text.

    Returns:
        Filename-safe slug string.
    """
    slug = title.lower()
    slug = slug.replace(" ", "-")
    slug = re.sub(r"[^a-z0-9-]", "", slug)
    slug = re.sub(r"-+", "-", slug)
    slug = slug.strip("-")
    return slug[:30].rstrip("-")


def _validate_choice(
    value: str,
    valid: frozenset[str],
    label: str,
) -> None:
    """Check a value against a set of valid choices.

    Args:
        value: Value to validate.
        valid: Set of allowed values.
        label: Human-readable label for error messages.

    Raises:
        ValueError: If value is not in the valid set.
    """
    if value not in valid:
        options = ", ".join(sorted(valid))
        msg = f"Invalid {label} '{value}'. Valid options: {options}"
        raise ValueError(msg)
