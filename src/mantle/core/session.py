"""Session logging — structured records of work done, decisions, and next steps."""

from __future__ import annotations

import warnings
from datetime import datetime
from typing import TYPE_CHECKING

import pydantic

from mantle.core import state, vault

if TYPE_CHECKING:
    from pathlib import Path


# ── Data model ───────────────────────────────────────────────────


class SessionNote(pydantic.BaseModel, frozen=True):
    """Session log frontmatter schema.

    Attributes:
        project: Project name from state.md.
        author: Git email of the session author.
        date: Datetime the session log was saved.
        commands_used: Mantle commands used during the session.
        tags: Mantle tags for categorization.
    """

    project: str
    author: str
    date: datetime
    commands_used: tuple[str, ...] = ()
    tags: tuple[str, ...] = ("type/session-log",)


# ── Constants ────────────────────────────────────────────────────

WORD_CAP: int = 200


# ── Warning ──────────────────────────────────────────────────────


class SessionTooLongWarning(UserWarning):
    """Issued when a session log exceeds the ~200 word cap."""


# ── Public API ───────────────────────────────────────────────────


def save_session(
    project_dir: Path,
    content: str,
    *,
    commands_used: tuple[str, ...] = (),
) -> tuple[SessionNote, Path]:
    """Save session log to .mantle/sessions/<date>-<HHMM>.md.

    Reads project name from state.md. Resolves author via git
    identity. Issues SessionTooLongWarning if body exceeds
    WORD_CAP.

    Args:
        project_dir: Directory containing .mantle/.
        content: Session log body (markdown).
        commands_used: Mantle commands used during the session.

    Returns:
        Tuple of (SessionNote frontmatter, path to saved file).
    """
    project_state = state.load_state(project_dir)
    identity = state.resolve_git_identity()

    session_path, now = _resolve_session_path(project_dir)

    note = SessionNote(
        project=project_state.project,
        author=identity,
        date=now,
        commands_used=commands_used,
    )

    vault.write_note(session_path, note, content)

    words = count_words(content)
    if words > WORD_CAP:
        warnings.warn(
            f"Session log exceeds ~{WORD_CAP} word cap ({words} words).",
            SessionTooLongWarning,
            stacklevel=2,
        )

    return note, session_path


def load_session(path: Path) -> tuple[SessionNote, str]:
    """Read a session log file.

    Takes absolute path (composable with list_sessions).

    Args:
        path: Absolute path to the session log file.

    Returns:
        Tuple of (SessionNote frontmatter, body text).

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    note = vault.read_note(path, SessionNote)
    return note.frontmatter, note.body


def list_sessions(
    project_dir: Path,
    *,
    author: str | None = None,
) -> list[Path]:
    """All session log paths, sorted oldest-first.

    Args:
        project_dir: Directory containing .mantle/.
        author: If provided, filter to sessions by this author.

    Returns:
        List of paths to session log files. Empty if none.
    """
    sessions_dir = project_dir / ".mantle" / "sessions"
    if not sessions_dir.is_dir():
        return []

    paths = sorted(sessions_dir.glob("*.md"))

    if author is not None:
        paths = [
            p
            for p in paths
            if vault.read_note(p, SessionNote).frontmatter.author == author
        ]

    return paths


def session_exists(project_dir: Path) -> bool:
    """True if at least one session log exists.

    Args:
        project_dir: Directory containing .mantle/.

    Returns:
        True if any session log files exist.
    """
    return len(list_sessions(project_dir)) > 0


def latest_session(
    project_dir: Path,
    *,
    author: str | None = None,
) -> tuple[SessionNote, str] | None:
    """Return the most recent session log.

    Args:
        project_dir: Directory containing .mantle/.
        author: If provided, filter to sessions by this author.

    Returns:
        Tuple of (SessionNote frontmatter, body text) for the
        latest session, or ``None`` if no matching sessions exist.
    """
    paths = list_sessions(project_dir, author=author)
    if not paths:
        return None
    return load_session(paths[-1])


def count_words(text: str) -> int:
    """Count words in text.

    Args:
        text: Text to count words in.

    Returns:
        Number of words.
    """
    return len(text.split())


# ── Internal helpers ─────────────────────────────────────────────


def _resolve_session_path(
    project_dir: Path,
) -> tuple[Path, datetime]:
    """Generate non-colliding session log path from current datetime.

    Format: .mantle/sessions/<date>-<HHMM>.md
    Auto-increments on collision: -2, -3, etc.
    Creates sessions/ directory if missing.

    Args:
        project_dir: Directory containing .mantle/.

    Returns:
        Tuple of (resolved path, datetime used).
    """
    sessions_dir = project_dir / ".mantle" / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    stem = now.strftime("%Y-%m-%d-%H%M")
    base = sessions_dir / f"{stem}.md"

    if not base.exists():
        return base, now

    counter = 2
    while True:
        path = sessions_dir / f"{stem}-{counter}.md"
        if not path.exists():
            return path, now
        counter += 1
