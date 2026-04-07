"""Shaped issues — evaluate approaches before decomposing into stories."""

from __future__ import annotations

import re
from datetime import date
from typing import TYPE_CHECKING

import pydantic

from mantle.core import issues, state, vault

if TYPE_CHECKING:
    from pathlib import Path


# ── Data model ───────────────────────────────────────────────────


class ShapedIssueNote(pydantic.BaseModel, frozen=True):
    """Shaped issue frontmatter schema.

    Attributes:
        issue: Issue number being shaped.
        title: Short title for the shaped issue.
        approaches: Approaches that were evaluated.
        chosen_approach: The selected approach name.
        appetite: Time/effort budget for this work.
        open_questions: Unresolved questions, if any.
        author: Git email of the author.
        created: Date the shaped issue was first saved.
        updated: Date of the last update.
        updated_by: Git email of the last updater.
        tags: Mantle tags for categorization.
    """

    issue: int
    title: str
    approaches: tuple[str, ...]
    chosen_approach: str
    appetite: str
    open_questions: tuple[str, ...] = ()
    author: str
    created: date
    updated: date
    updated_by: str
    tags: tuple[str, ...] = ("type/shaped", "phase/shaping")


# ── Exception ────────────────────────────────────────────────────


class ShapedIssueExistsError(Exception):
    """Raised when a shaped issue already exists for this issue number.

    Attributes:
        path: Path to the existing shaped issue file.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        super().__init__(f"Shaped issue already exists at {path}")


# ── Public API ───────────────────────────────────────────────────


def save_shaped_issue(
    project_dir: Path,
    content: str,
    *,
    issue: int,
    title: str,
    approaches: tuple[str, ...],
    chosen_approach: str,
    appetite: str,
    open_questions: tuple[str, ...] = (),
    overwrite: bool = False,
) -> tuple[ShapedIssueNote, Path]:
    """Save shaped issue to .mantle/shaped/issue-NN-shaped.md.

    One file per issue. Raises if exists and overwrite is False.
    Updates state.md Current Focus after saving.

    Args:
        project_dir: Directory containing .mantle/.
        content: Full shaping write-up body.
        issue: Issue number being shaped.
        title: Short title for the shaped issue.
        approaches: Approaches that were evaluated.
        chosen_approach: The selected approach name.
        appetite: Time/effort budget for this work.
        open_questions: Unresolved questions, if any.
        overwrite: Replace existing shaped issue file.

    Returns:
        Tuple of (ShapedIssueNote frontmatter, path to saved file).

    Raises:
        ShapedIssueExistsError: If file exists and overwrite is False.
    """
    shaped_path = _shaped_issue_path(project_dir, issue, title)

    if shaped_path.exists() and not overwrite:
        raise ShapedIssueExistsError(shaped_path)

    identity = state.resolve_git_identity()
    today = date.today()

    if overwrite and shaped_path.exists():
        existing = vault.read_note(shaped_path, ShapedIssueNote)
        created = existing.frontmatter.created
    else:
        created = today

    note = ShapedIssueNote(
        issue=issue,
        title=title,
        approaches=approaches,
        chosen_approach=chosen_approach,
        appetite=appetite,
        open_questions=open_questions,
        author=identity,
        created=created,
        updated=today,
        updated_by=identity,
    )

    vault.write_note(shaped_path, note, content)
    _update_state_body(project_dir, identity, issue)

    return note, shaped_path


def load_shaped_issue(path: Path) -> tuple[ShapedIssueNote, str]:
    """Read a shaped issue file.

    Takes absolute path (composable with list_shaped_issues).

    Args:
        path: Absolute path to the shaped issue file.

    Returns:
        Tuple of (ShapedIssueNote frontmatter, body text).

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    note = vault.read_note(path, ShapedIssueNote)
    return note.frontmatter, note.body


def list_shaped_issues(project_dir: Path) -> list[Path]:
    """All shaped issue paths, sorted oldest-first.

    Args:
        project_dir: Directory containing .mantle/.

    Returns:
        List of paths to shaped issue files. Empty if none.
    """
    shaped_dir = project_dir / ".mantle" / "shaped"
    if not shaped_dir.is_dir():
        return []
    return sorted(shaped_dir.glob("issue-*-shaped.md"))


def shaped_issue_exists(project_dir: Path, issue: int) -> bool:
    """True if a shaped issue file exists for the given issue number.

    Args:
        project_dir: Directory containing .mantle/.
        issue: Issue number to check.

    Returns:
        True if the shaped issue file exists.
    """
    return find_shaped_issue_path(project_dir, issue) is not None


# ── Internal helpers ─────────────────────────────────────────────


def _shaped_issue_path(
    project_dir: Path,
    issue: int,
    title: str = "",
) -> Path:
    """Compute shaped issue file path with slug.

    Args:
        project_dir: Directory containing .mantle/.
        issue: Issue number.
        title: Issue title (slugified for filename).

    Returns:
        Path for the shaped issue file.
    """
    slug = issues._slugify_title(title) if title else ""
    if slug:
        return (
            project_dir
            / ".mantle"
            / "shaped"
            / f"issue-{issue:02d}-{slug}-shaped.md"
        )
    return project_dir / ".mantle" / "shaped" / f"issue-{issue:02d}-shaped.md"


def find_shaped_issue_path(project_dir: Path, issue: int) -> Path | None:
    """Find a shaped issue file by number using glob lookup.

    Args:
        project_dir: Directory containing .mantle/.
        issue: Issue number.

    Returns:
        Path to the shaped issue file, or None if not found.
    """
    shaped_dir = project_dir / ".mantle" / "shaped"
    matches = sorted(shaped_dir.glob(f"issue-{issue:02d}-*-shaped.md"))
    if matches:
        return matches[0]
    # Fallback to old naming convention
    old = shaped_dir / f"issue-{issue:02d}-shaped.md"
    return old if old.exists() else None


def _update_state_body(
    project_dir: Path,
    identity: str,
    issue: int,
) -> None:
    """Update state.md Current Focus after shaping.

    Overwrites Current Focus section content. Does not
    transition state — stays in PLANNING.

    Args:
        project_dir: Directory containing .mantle/.
        identity: Git email for the updated_by field.
        issue: Issue number that was shaped.
    """
    state_path = project_dir / ".mantle" / "state.md"
    note = vault.read_note(state_path, state.ProjectState)

    body = re.sub(
        r"(## Current Focus\n\n).*?(?=\n##|\Z)",
        rf"\1Issue {issue} shaped"
        r" — run /mantle:plan-stories next."
        "\n",
        note.body,
        count=1,
        flags=re.DOTALL,
    )

    updated = note.frontmatter.model_copy(
        update={
            "updated": date.today(),
            "updated_by": identity,
        },
    )

    vault.write_note(state_path, updated, body)
