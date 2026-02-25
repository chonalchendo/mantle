"""System design document — architecture and technical decisions."""

from __future__ import annotations

import re
from datetime import date
from typing import TYPE_CHECKING

import pydantic

from mantle.core import state, vault

if TYPE_CHECKING:
    from pathlib import Path


# ── Data model ───────────────────────────────────────────────────


class SystemDesignNote(pydantic.BaseModel, frozen=True):
    """System-design.md frontmatter schema.

    Attributes:
        author: Git email of the document author.
        created: Date the document was created.
        updated: Date of the last edit.
        updated_by: Git email of the last editor.
        tags: Mantle tags for categorization.
    """

    author: str
    created: date
    updated: date
    updated_by: str
    tags: tuple[str, ...] = (
        "type/system-design",
        "phase/system-design",
    )


# ── Exception ────────────────────────────────────────────────────


class SystemDesignExistsError(Exception):
    """Raised when system-design.md already exists and overwrite is False.

    Attributes:
        path: Path to the existing system-design.md file.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        super().__init__(f"System design already exists: {path}")


# ── Public API ───────────────────────────────────────────────────


def save_system_design(
    project_dir: Path,
    content: str,
    *,
    overwrite: bool = False,
) -> SystemDesignNote:
    """Write .mantle/system-design.md and transition state.

    Transitions state to system-design first (fail fast), then
    writes the document, then updates state body Current Focus.

    Args:
        project_dir: Directory containing .mantle/.
        content: Full system design document body.
        overwrite: Replace existing system-design.md if True.

    Returns:
        The created SystemDesignNote.

    Raises:
        SystemDesignExistsError: If file exists and overwrite
            is False.
        InvalidTransitionError: If state is not product-design.
    """
    design_path = project_dir / ".mantle" / "system-design.md"

    if design_path.exists() and not overwrite:
        raise SystemDesignExistsError(design_path)

    # Fail fast: transition state before writing document
    state.transition(project_dir, state.Status.SYSTEM_DESIGN)

    identity = state.resolve_git_identity()
    today = date.today()

    note = SystemDesignNote(
        author=identity,
        created=today,
        updated=today,
        updated_by=identity,
    )

    vault.write_note(design_path, note, content)
    _update_state_body(project_dir, identity)

    return note


def load_system_design(
    project_dir: Path,
) -> tuple[SystemDesignNote, str]:
    """Read .mantle/system-design.md.

    Args:
        project_dir: Directory containing .mantle/.

    Returns:
        Tuple of (SystemDesignNote frontmatter, body text).

    Raises:
        FileNotFoundError: If system-design.md does not exist.
    """
    path = project_dir / ".mantle" / "system-design.md"
    note = vault.read_note(path, SystemDesignNote)
    return note.frontmatter, note.body


def system_design_exists(project_dir: Path) -> bool:
    """Check whether .mantle/system-design.md exists.

    Args:
        project_dir: Directory containing .mantle/.

    Returns:
        True if system-design.md exists, False otherwise.
    """
    return (project_dir / ".mantle" / "system-design.md").exists()


# ── Internal helpers ─────────────────────────────────────────────


def _update_state_body(
    project_dir: Path,
    identity: str,
) -> None:
    """Update state.md body with next step and refresh timestamps.

    Args:
        project_dir: Directory containing .mantle/.
        identity: Git email for the updated_by field.
    """
    state_path = project_dir / ".mantle" / "state.md"
    note = vault.read_note(state_path, state.ProjectState)

    body = re.sub(
        r"(## Current Focus\n\n).*?(?=\n##|\Z)",
        (
            r"\1System design complete"
            " — run /mantle:plan-issues next.\n"
        ),
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
