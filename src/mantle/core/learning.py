"""Learning notes — capture implementation learnings per issue."""

from __future__ import annotations

import re
from datetime import date
from typing import TYPE_CHECKING

import pydantic

from mantle.core import state, vault

if TYPE_CHECKING:
    from pathlib import Path


# ── Data model ───────────────────────────────────────────────────


class LearningNote(pydantic.BaseModel, frozen=True):
    """Learning note frontmatter schema.

    Attributes:
        issue: Issue number this learning relates to.
        title: Short title for the learning.
        author: Git email of the author.
        date: Date the learning was saved.
        confidence_delta: Change in confidence (e.g. "+2", "-1").
        tags: Mantle tags for categorization.
    """

    issue: int
    title: str
    author: str
    date: date
    confidence_delta: str
    tags: tuple[str, ...] = ("type/learning", "phase/reviewing")


# ── Exception ────────────────────────────────────────────────────


class LearningExistsError(Exception):
    """Raised when a learning already exists for this issue number.

    Attributes:
        path: Path to the existing learning file.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        super().__init__(f"Learning already exists at {path}")


# ── Public API ───────────────────────────────────────────────────


def save_learning(
    project_dir: Path,
    content: str,
    *,
    issue: int,
    title: str,
    confidence_delta: str,
    overwrite: bool = False,
) -> tuple[LearningNote, Path]:
    """Save learning to .mantle/learnings/issue-NN.md.

    One file per issue. Raises if exists and overwrite is False.
    Validates confidence_delta format. Updates state.md Current Focus.

    Args:
        project_dir: Directory containing .mantle/.
        content: Structured reflection body.
        issue: Issue number this learning relates to.
        title: Short title for the learning.
        confidence_delta: Confidence change (e.g. "+2", "-1").
        overwrite: Replace existing learning file.

    Returns:
        Tuple of (LearningNote frontmatter, path to saved file).

    Raises:
        LearningExistsError: If file exists and overwrite is False.
        ValueError: If confidence_delta format is invalid.
    """
    _validate_confidence_delta(confidence_delta)

    learning_path = _learning_path(project_dir, issue)

    if learning_path.exists() and not overwrite:
        raise LearningExistsError(learning_path)

    identity = state.resolve_git_identity()
    today = date.today()

    note = LearningNote(
        issue=issue,
        title=title,
        author=identity,
        date=today,
        confidence_delta=confidence_delta,
    )

    vault.write_note(learning_path, note, content)
    _update_state_body(project_dir, identity, issue)

    return note, learning_path


def load_learning(path: Path) -> tuple[LearningNote, str]:
    """Read a learning file.

    Takes absolute path (composable with list_learnings).

    Args:
        path: Absolute path to the learning file.

    Returns:
        Tuple of (LearningNote frontmatter, body text).

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    note = vault.read_note(path, LearningNote)
    return note.frontmatter, note.body


def list_learnings(project_dir: Path) -> list[Path]:
    """All learning paths, sorted oldest-first.

    Args:
        project_dir: Directory containing .mantle/.

    Returns:
        List of paths to learning files. Empty if none.
    """
    learnings_dir = project_dir / ".mantle" / "learnings"
    if not learnings_dir.is_dir():
        return []
    return sorted(learnings_dir.glob("issue-*.md"))


def learning_exists(project_dir: Path, issue: int) -> bool:
    """True if a learning file exists for the given issue number.

    Args:
        project_dir: Directory containing .mantle/.
        issue: Issue number to check.

    Returns:
        True if the learning file exists.
    """
    return _learning_path(project_dir, issue).exists()


# ── Internal helpers ─────────────────────────────────────────────


def _validate_confidence_delta(confidence_delta: str) -> None:
    """Validate confidence_delta format.

    Args:
        confidence_delta: String to validate.

    Raises:
        ValueError: If format does not match [+-]\\d{1,2}.
    """
    if not re.fullmatch(r"[+-]\d{1,2}", confidence_delta):
        msg = (
            f"Invalid confidence_delta '{confidence_delta}'. "
            f"Must match [+-]N format (e.g. '+2', '-1')"
        )
        raise ValueError(msg)


def _learning_path(project_dir: Path, issue: int) -> Path:
    """Compute learning file path.

    Args:
        project_dir: Directory containing .mantle/.
        issue: Issue number.

    Returns:
        Path for the learning file.
    """
    return project_dir / ".mantle" / "learnings" / f"issue-{issue:02d}.md"


def _update_state_body(
    project_dir: Path,
    identity: str,
    issue: int,
) -> None:
    """Update state.md Current Focus after capturing a learning.

    Overwrites Current Focus section content. Does not
    transition state.

    Args:
        project_dir: Directory containing .mantle/.
        identity: Git email for the updated_by field.
        issue: Issue number the learning was captured for.
    """
    state_path = project_dir / ".mantle" / "state.md"
    note = vault.read_note(state_path, state.ProjectState)

    body = re.sub(
        r"(## Current Focus\n\n).*?(?=\n##|\Z)",
        rf"\1Learning captured for issue {issue}"
        r" — review past learnings before next"
        r" planning cycle."
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
