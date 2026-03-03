"""Bug capture — structured bug reports with severity and status tracking."""

from __future__ import annotations

import re
from datetime import date
from typing import TYPE_CHECKING

import pydantic

from mantle.core import state, vault

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path


# ── Constants ───────────────────────────────────────────────────

VALID_SEVERITIES: frozenset[str] = frozenset(
    {"blocker", "high", "medium", "low"}
)
VALID_STATUSES: frozenset[str] = frozenset(
    {"open", "fixed", "wont-fix"}
)


# ── Data model ──────────────────────────────────────────────────


class BugNote(pydantic.BaseModel, frozen=True):
    """Bug report frontmatter schema.

    Attributes:
        date: Date the bug was captured.
        author: Git email of the bug reporter.
        summary: One-line bug summary.
        severity: Bug severity (blocker, high, medium, low).
        status: Bug lifecycle status (open, fixed, wont-fix).
        related_issue: Optional related issue (e.g. "issue-08").
        related_files: Files involved in the bug.
        fixed_by: Issue that fixes this bug (e.g. "issue-21").
        tags: Mantle tags for categorization.
    """

    date: date
    author: str
    summary: str
    severity: str
    status: str = "open"
    related_issue: str | None = None
    related_files: tuple[str, ...] = ()
    fixed_by: str | None = None
    tags: tuple[str, ...] = ("type/bug", "status/open")


# ── Exception ───────────────────────────────────────────────────


class BugExistsError(Exception):
    """Raised when a bug file already exists at the target path.

    Attributes:
        path: Path to the existing bug file.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        super().__init__(f"Bug already exists at {path}")


# ── Public API ──────────────────────────────────────────────────


def create_bug(
    project_dir: Path,
    *,
    summary: str,
    severity: str,
    description: str,
    reproduction: str,
    expected: str,
    actual: str,
    related_issue: str | None = None,
    related_files: Sequence[str] = (),
) -> tuple[BugNote, Path]:
    """Save a bug report to .mantle/bugs/<date>-<slug>.md.

    Args:
        project_dir: Directory containing .mantle/.
        summary: One-line bug summary.
        severity: Bug severity (blocker, high, medium, low).
        description: What happened (paragraph).
        reproduction: Steps to reproduce.
        expected: Expected behaviour.
        actual: Actual behaviour.
        related_issue: Related issue identifier (optional).
        related_files: Related file paths (optional).

    Returns:
        Tuple of (BugNote frontmatter, path to saved file).

    Raises:
        ValueError: If severity is not valid.
        BugExistsError: If the bug file already exists.
    """
    _validate_choice(severity, VALID_SEVERITIES, "severity")

    identity = state.resolve_git_identity()
    today = date.today()
    slug = _slugify(summary)
    bug_path = _bug_path(project_dir, str(today), slug)

    if bug_path.exists():
        raise BugExistsError(bug_path)

    tags = ("type/bug", f"severity/{severity}", "status/open")

    note = BugNote(
        date=today,
        author=identity,
        summary=summary,
        severity=severity,
        related_issue=related_issue,
        related_files=tuple(related_files),
        tags=tags,
    )

    body = _build_bug_body(description, reproduction, expected, actual)
    vault.write_note(bug_path, note, body)

    return note, bug_path


def load_bug(path: Path) -> tuple[BugNote, str]:
    """Read a bug file by absolute path.

    Args:
        path: Absolute path to the bug file.

    Returns:
        Tuple of (BugNote frontmatter, body text).

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    note = vault.read_note(path, BugNote)
    return note.frontmatter, note.body


def list_bugs(
    project_dir: Path,
    *,
    status: str | None = None,
) -> list[Path]:
    """All bug paths in .mantle/bugs/, sorted oldest-first.

    Args:
        project_dir: Directory containing .mantle/.
        status: Filter to bugs matching this status (optional).

    Returns:
        List of paths to bug files. Empty if none.
    """
    bugs_dir = project_dir / ".mantle" / "bugs"
    if not bugs_dir.is_dir():
        return []

    paths = sorted(bugs_dir.glob("*.md"))

    if status is None:
        return paths

    filtered = []
    for path in paths:
        bug, _ = load_bug(path)
        if bug.status == status:
            filtered.append(path)
    return filtered


def update_bug_status(
    project_dir: Path,
    bug_filename: str,
    *,
    status: str,
    fixed_by: str | None = None,
) -> tuple[BugNote, str]:
    """Update a bug's status and optionally set fixed_by.

    Args:
        project_dir: Directory containing .mantle/.
        bug_filename: Bug filename (e.g. "2026-03-03-slug.md").
        status: New status (open, fixed, wont-fix).
        fixed_by: Issue that fixes this bug (optional).

    Returns:
        Tuple of (updated BugNote, previous status string).

    Raises:
        FileNotFoundError: If the bug file does not exist.
        ValueError: If the status is not valid.
    """
    _validate_choice(status, VALID_STATUSES, "status")

    bug_path = project_dir / ".mantle" / "bugs" / bug_filename

    try:
        note = vault.read_note(bug_path, BugNote)
    except FileNotFoundError:
        msg = f"Bug not found: {bug_path}"
        raise FileNotFoundError(msg) from None

    current = note.frontmatter

    # Update tags: replace old status tag with new one
    old_status_tag = f"status/{current.status}"
    new_status_tag = f"status/{status}"
    tags = tuple(
        new_status_tag if t == old_status_tag else t
        for t in current.tags
    )

    updates: dict[str, object] = {
        "status": status,
        "tags": tags,
    }
    if fixed_by is not None:
        updates["fixed_by"] = fixed_by

    old_status = current.status
    updated = current.model_copy(update=updates)
    vault.write_note(bug_path, updated, note.body)

    return updated, old_status


# ── Internal helpers ────────────────────────────────────────────


def _bug_path(project_dir: Path, date_str: str, slug: str) -> Path:
    """Compute bug file path.

    Args:
        project_dir: Directory containing .mantle/.
        date_str: Date string (YYYY-MM-DD).
        slug: Slugified summary.

    Returns:
        Path for the bug file.
    """
    return (
        project_dir / ".mantle" / "bugs" / f"{date_str}-{slug}.md"
    )


def _slugify(summary: str) -> str:
    """Convert summary to filename-safe slug.

    Lowercase, replace spaces with hyphens, strip non-alphanumeric
    characters (except hyphens), truncate to 50 chars.

    Args:
        summary: The bug summary text.

    Returns:
        Filename-safe slug string.
    """
    slug = summary.lower()
    slug = slug.replace(" ", "-")
    slug = re.sub(r"[^a-z0-9-]", "", slug)
    slug = re.sub(r"-+", "-", slug)
    slug = slug.strip("-")
    return slug[:50]


def _build_bug_body(
    description: str,
    reproduction: str,
    expected: str,
    actual: str,
) -> str:
    """Build the markdown body from bug content.

    Args:
        description: What happened (paragraph).
        reproduction: Steps or context to reproduce.
        expected: What should happen.
        actual: What actually happens.

    Returns:
        Formatted markdown body string.
    """
    return (
        f"## Description\n\n{description}\n\n"
        f"## Reproduction\n\n{reproduction}\n\n"
        f"## Expected Behaviour\n\n{expected}\n\n"
        f"## Actual Behaviour\n\n{actual}\n"
    )


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
        msg = (
            f"Invalid {label} '{value}'. "
            f"Valid options: {options}"
        )
        raise ValueError(msg)
