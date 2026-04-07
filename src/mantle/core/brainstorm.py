"""Brainstorm sessions — validate feature ideas against existing vision."""

from __future__ import annotations

import re
from datetime import date
from typing import TYPE_CHECKING

import pydantic

from mantle.core import sanitize, state, vault

if TYPE_CHECKING:
    from pathlib import Path


# -- Constants ----------------------------------------------------

VALID_VERDICTS: frozenset[str] = frozenset({"proceed", "research", "scrap"})


# -- Data model ---------------------------------------------------


class BrainstormNote(pydantic.BaseModel, frozen=True):
    """Brainstorm session frontmatter schema.

    Attributes:
        date: Date the brainstorm session was saved.
        author: Git email of the brainstormer.
        title: Short title describing the brainstorm topic.
        verdict: Outcome verdict (one of VALID_VERDICTS).
        tags: Mantle tags for categorization.
    """

    date: date
    author: str
    title: str
    verdict: str
    tags: tuple[str, ...] = ("type/brainstorm",)


# -- Public API ---------------------------------------------------


def save_brainstorm(
    project_dir: Path,
    content: str,
    *,
    title: str,
    verdict: str,
) -> tuple[BrainstormNote, Path]:
    """Save content to .mantle/brainstorms/<date>-<slug>.md.

    Auto-increments filename on same-day same-slug collision
    (-2, -3, ...).  Updates state.md Current Focus after saving.

    Args:
        project_dir: Directory containing .mantle/.
        content: Brainstorm session body content.
        title: Short title for the brainstorm topic.
        verdict: Outcome verdict (must be in VALID_VERDICTS).

    Returns:
        Tuple of (BrainstormNote frontmatter, path to saved file).

    Raises:
        ValueError: If verdict is not in VALID_VERDICTS.
    """
    if verdict not in VALID_VERDICTS:
        msg = (
            f"Invalid verdict '{verdict}'. "
            f"Must be one of: {', '.join(sorted(VALID_VERDICTS))}"
        )
        raise ValueError(msg)

    identity = state.resolve_git_identity()
    today = date.today()

    note = BrainstormNote(
        date=today,
        author=identity,
        title=title,
        verdict=verdict,
    )

    brainstorm_path = _resolve_brainstorm_path(project_dir, title)
    vault.write_note(
        brainstorm_path,
        note,
        sanitize.strip_analysis_blocks(content),
    )
    _update_state_body(project_dir, identity, verdict)

    return note, brainstorm_path


def load_brainstorm(path: Path) -> tuple[BrainstormNote, str]:
    """Read a brainstorm file.

    Takes absolute path (composable with list_brainstorms).

    Args:
        path: Absolute path to the brainstorm file.

    Returns:
        Tuple of (BrainstormNote frontmatter, body text).

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    note = vault.read_note(path, BrainstormNote)
    return note.frontmatter, note.body


def list_brainstorms(project_dir: Path) -> list[Path]:
    """All brainstorm paths, sorted oldest-first.

    Args:
        project_dir: Directory containing .mantle/.

    Returns:
        List of paths to brainstorm files. Empty if none.
    """
    brainstorms_dir = project_dir / ".mantle" / "brainstorms"
    if not brainstorms_dir.is_dir():
        return []
    return sorted(brainstorms_dir.glob("*.md"))


def brainstorm_exists(project_dir: Path) -> bool:
    """True if at least one brainstorm session exists.

    Args:
        project_dir: Directory containing .mantle/.

    Returns:
        True if any brainstorm files exist.
    """
    return len(list_brainstorms(project_dir)) > 0


# -- Internal helpers ---------------------------------------------


def _slugify(title: str) -> str:
    """Lowercase, replace non-alphanumeric with hyphens, truncate.

    Args:
        title: Human-readable title string.

    Returns:
        URL-safe slug, max 40 characters.
    """
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug[:40]


def _resolve_brainstorm_path(project_dir: Path, title: str) -> Path:
    """Compute non-colliding brainstorm file path with auto-increment.

    Args:
        project_dir: Directory containing .mantle/.
        title: Brainstorm title used to generate filename slug.

    Returns:
        Path for the new brainstorm file.
    """
    brainstorms_dir = project_dir / ".mantle" / "brainstorms"
    today = date.today().isoformat()
    slug = _slugify(title)
    base = brainstorms_dir / f"{today}-{slug}.md"

    if not base.exists():
        return base

    counter = 2
    while True:
        path = brainstorms_dir / f"{today}-{slug}-{counter}.md"
        if not path.exists():
            return path
        counter += 1


_VERDICT_MESSAGES: dict[str, str] = {
    "proceed": (
        "Brainstorm completed (proceed)"
        " — idea validated, ready for next steps.\n"
    ),
    "research": (
        "Brainstorm completed (research)"
        " — needs more research before proceeding.\n"
    ),
    "scrap": (
        "Brainstorm completed (scrap) — idea scrapped, context preserved.\n"
    ),
}


def _update_state_body(
    project_dir: Path,
    identity: str,
    verdict: str,
) -> None:
    """Update state.md body with brainstorm verdict message.

    Overwrites Current Focus section content (not fragile
    placeholder search).

    Args:
        project_dir: Directory containing .mantle/.
        identity: Git email for the updated_by field.
        verdict: Brainstorm verdict for the message.
    """
    state_path = project_dir / ".mantle" / "state.md"
    note = vault.read_note(state_path, state.ProjectState)

    message = _VERDICT_MESSAGES[verdict]
    body = re.sub(
        r"(## Current Focus\n\n).*?(?=\n##|\Z)",
        rf"\1{message}",
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
