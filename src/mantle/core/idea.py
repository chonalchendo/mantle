"""Idea capture — structured hypothesis with success criteria."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

import pydantic

from mantle.core import state, vault

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path


# ── Data model ───────────────────────────────────────────────────


class IdeaNote(pydantic.BaseModel, frozen=True):
    """Idea.md frontmatter schema.

    Attributes:
        hypothesis: Core belief or value proposition.
        target_user: Who this idea is for.
        success_criteria: Measurable outcomes that prove success.
        author: Git email of the idea author.
        created: Date the idea was captured.
        updated: Date of the last edit.
        updated_by: Git email of the last editor.
        tags: Mantle tags for categorization.
    """

    hypothesis: str
    target_user: str
    success_criteria: tuple[str, ...]
    author: str
    created: date
    updated: date
    updated_by: str
    tags: tuple[str, ...] = ("type/idea", "phase/idea")


# ── Exception ────────────────────────────────────────────────────


class IdeaExistsError(Exception):
    """Raised when idea.md already exists and overwrite is False.

    Attributes:
        path: Path to the existing idea.md file.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        super().__init__(f"Idea already exists: {path}")


# ── Body template ────────────────────────────────────────────────


_IDEA_BODY = """\
## Hypothesis

_What do you believe to be true?_

## Target User

_Who is this for?_

## Success Criteria

_How will you know this worked?_

## Open Questions

_What do you still need to learn?_
"""


# ── Public API ───────────────────────────────────────────────────


def create_idea(
    project_dir: Path,
    *,
    hypothesis: str,
    target_user: str,
    success_criteria: Sequence[str],
    overwrite: bool = False,
) -> IdeaNote:
    """Write .mantle/idea.md and update state.md body.

    Args:
        project_dir: Directory containing .mantle/.
        hypothesis: Core belief or value proposition.
        target_user: Who this idea is for.
        success_criteria: Measurable outcomes that prove success.
        overwrite: Replace existing idea.md if True.

    Returns:
        The created IdeaNote.

    Raises:
        IdeaExistsError: If idea.md exists and overwrite is False.
    """
    idea_path = project_dir / ".mantle" / "idea.md"

    if idea_path.exists() and not overwrite:
        raise IdeaExistsError(idea_path)

    identity = state.resolve_git_identity()
    today = date.today()

    note = IdeaNote(
        hypothesis=hypothesis,
        target_user=target_user,
        success_criteria=tuple(success_criteria),
        author=identity,
        created=today,
        updated=today,
        updated_by=identity,
    )

    vault.write_note(idea_path, note, _IDEA_BODY)
    _update_state_body(project_dir, hypothesis, identity)

    return note


def load_idea(project_dir: Path) -> IdeaNote:
    """Read .mantle/idea.md and return the idea note.

    Args:
        project_dir: Directory containing .mantle/.

    Returns:
        The current IdeaNote.

    Raises:
        FileNotFoundError: If idea.md does not exist.
    """
    path = project_dir / ".mantle" / "idea.md"
    note = vault.read_note(path, IdeaNote)
    return note.frontmatter


def update_idea(
    project_dir: Path,
    *,
    hypothesis: str | None = None,
    target_user: str | None = None,
    success_criteria: Sequence[str] | None = None,
) -> IdeaNote:
    """Update idea fields without replacing. Refreshes timestamps.

    Args:
        project_dir: Directory containing .mantle/.
        hypothesis: New hypothesis, or None to keep current.
        target_user: New target user, or None to keep current.
        success_criteria: New criteria, or None to keep current.

    Returns:
        The updated IdeaNote.

    Raises:
        FileNotFoundError: If idea.md does not exist.
    """
    idea_path = project_dir / ".mantle" / "idea.md"
    note = vault.read_note(idea_path, IdeaNote)
    current = note.frontmatter

    identity = state.resolve_git_identity()
    updates: dict[str, object] = {
        "updated": date.today(),
        "updated_by": identity,
    }
    if hypothesis is not None:
        updates["hypothesis"] = hypothesis
    if target_user is not None:
        updates["target_user"] = target_user
    if success_criteria is not None:
        updates["success_criteria"] = tuple(success_criteria)

    updated = current.model_copy(update=updates)
    vault.write_note(idea_path, updated, note.body)
    return updated


def idea_exists(project_dir: Path) -> bool:
    """Check whether .mantle/idea.md exists.

    Args:
        project_dir: Directory containing .mantle/.

    Returns:
        True if idea.md exists, False otherwise.
    """
    return (project_dir / ".mantle" / "idea.md").exists()


# ── Internal helpers ─────────────────────────────────────────────


def _update_state_body(
    project_dir: Path,
    hypothesis: str,
    identity: str,
) -> None:
    """Update state.md body with idea summary and refresh timestamps.

    Replaces known placeholder text in the Summary and Current Focus
    sections, then refreshes the updated/updated_by frontmatter fields.

    Args:
        project_dir: Directory containing .mantle/.
        hypothesis: Idea hypothesis to insert into Summary.
        identity: Git email for the updated_by field.
    """
    state_path = project_dir / ".mantle" / "state.md"
    note = vault.read_note(state_path, state.ProjectState)

    body = note.body
    body = body.replace(
        "_Describe the project in one or two sentences._",
        hypothesis,
    )
    body = body.replace(
        "_What are you working on right now?_",
        "Idea captured — run /mantle:challenge next.",
    )

    updated = note.frontmatter.model_copy(
        update={
            "updated": date.today(),
            "updated_by": identity,
        },
    )

    vault.write_note(state_path, updated, body)
