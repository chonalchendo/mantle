"""Challenge session — stress-test an idea from multiple angles."""

from __future__ import annotations

import re
from datetime import date
from typing import TYPE_CHECKING

import pydantic

from mantle.core import state, vault

if TYPE_CHECKING:
    from pathlib import Path


# ── Data model ───────────────────────────────────────────────────


class ChallengeNote(pydantic.BaseModel, frozen=True):
    """Challenge transcript frontmatter schema.

    Attributes:
        date: Date the challenge session was saved.
        author: Git email of the challenger.
        hypothesis_ref: Snapshot of the hypothesis being challenged.
        tags: Mantle tags for categorization.
    """

    date: date
    author: str
    hypothesis_ref: str
    tags: tuple[str, ...] = ("type/challenge", "phase/challenge")


# ── Exception ────────────────────────────────────────────────────


class IdeaNotFoundError(Exception):
    """Raised when save_challenge is called without idea.md.

    Attributes:
        path: Expected path to idea.md.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        super().__init__(f"No idea.md found at {path}")


# ── Public API ───────────────────────────────────────────────────


def save_challenge(
    project_dir: Path,
    transcript: str,
) -> tuple[ChallengeNote, Path]:
    """Save transcript to .mantle/challenges/<date>-challenge.md.

    Auto-increments filename on same-day collision (-2, -3, ...).
    Reads idea.md to snapshot hypothesis_ref.
    Updates state.md Current Focus after saving.

    Args:
        project_dir: Directory containing .mantle/.
        transcript: Full challenge session transcript.

    Returns:
        Tuple of (ChallengeNote frontmatter, path to saved file).

    Raises:
        IdeaNotFoundError: If idea.md does not exist.
    """
    idea_path = project_dir / ".mantle" / "idea.md"
    if not idea_path.exists():
        raise IdeaNotFoundError(idea_path)

    from mantle.core import idea

    idea_note = idea.load_idea(project_dir)
    identity = state.resolve_git_identity()
    today = date.today()

    note = ChallengeNote(
        date=today,
        author=identity,
        hypothesis_ref=idea_note.hypothesis,
    )

    challenge_path = _resolve_challenge_path(project_dir)
    vault.write_note(challenge_path, note, transcript)
    _update_state_body(project_dir, identity)

    return note, challenge_path


def load_challenge(path: Path) -> tuple[ChallengeNote, str]:
    """Read a challenge file.

    Takes absolute path (composable with list_challenges).

    Args:
        path: Absolute path to the challenge file.

    Returns:
        Tuple of (ChallengeNote frontmatter, body text).

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    note = vault.read_note(path, ChallengeNote)
    return note.frontmatter, note.body


def list_challenges(project_dir: Path) -> list[Path]:
    """All challenge paths, sorted oldest-first.

    Args:
        project_dir: Directory containing .mantle/.

    Returns:
        List of paths to challenge files. Empty if none.
    """
    challenges_dir = project_dir / ".mantle" / "challenges"
    if not challenges_dir.is_dir():
        return []
    return sorted(challenges_dir.glob("*-challenge*.md"))


def challenge_exists(project_dir: Path) -> bool:
    """True if at least one challenge transcript exists.

    Args:
        project_dir: Directory containing .mantle/.

    Returns:
        True if any challenge files exist.
    """
    return len(list_challenges(project_dir)) > 0


# ── Internal helpers ─────────────────────────────────────────────


def _resolve_challenge_path(project_dir: Path) -> Path:
    """Compute non-colliding challenge file path with auto-increment.

    Args:
        project_dir: Directory containing .mantle/.

    Returns:
        Path for the new challenge file.
    """
    challenges_dir = project_dir / ".mantle" / "challenges"
    today = date.today().isoformat()
    base = challenges_dir / f"{today}-challenge.md"

    if not base.exists():
        return base

    counter = 2
    while True:
        path = challenges_dir / f"{today}-challenge-{counter}.md"
        if not path.exists():
            return path
        counter += 1


def _update_state_body(project_dir: Path, identity: str) -> None:
    """Update state.md body with challenge summary and refresh timestamps.

    Overwrites Current Focus section content (not fragile placeholder
    search).

    Args:
        project_dir: Directory containing .mantle/.
        identity: Git email for the updated_by field.
    """
    state_path = project_dir / ".mantle" / "state.md"
    note = vault.read_note(state_path, state.ProjectState)

    body = re.sub(
        r"(## Current Focus\n\n).*?(?=\n##|\Z)",
        r"\1Challenge completed — run /mantle:design-product next.\n",
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
