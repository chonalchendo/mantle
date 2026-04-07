"""Scout reports — analyze external repos through project context."""

from __future__ import annotations

import re
from datetime import date
from typing import TYPE_CHECKING

import pydantic

from mantle.core import project, sanitize, state, vault

if TYPE_CHECKING:
    from pathlib import Path


# -- Data model ---------------------------------------------------


class ScoutReport(pydantic.BaseModel, frozen=True):
    """Scout report frontmatter schema.

    Attributes:
        date: Date the scout report was saved.
        author: Git email of the author.
        repo_url: Full URL of the scouted repository.
        repo_name: Short name of the scouted repository.
        dimensions: Analysis dimensions covered in the report.
        tags: Mantle tags for categorization.
    """

    date: date
    author: str
    repo_url: str
    repo_name: str
    dimensions: tuple[str, ...] = ()
    tags: tuple[str, ...] = ("type/scout",)


# -- Public API ---------------------------------------------------


def save_scout(
    project_dir: Path,
    content: str,
    *,
    repo_url: str,
    repo_name: str,
    dimensions: tuple[str, ...],
) -> tuple[ScoutReport, Path]:
    """Save content to .mantle/scouts/<date>-<repo-name-slug>.md.

    Auto-increments filename on same-day same-slug collision
    (-2, -3, ...).  Updates state.md Current Focus after saving.

    Args:
        project_dir: Directory containing .mantle/.
        content: Scout report body content.
        repo_url: Full URL of the scouted repository.
        repo_name: Short name of the scouted repository.
        dimensions: Analysis dimensions covered in the report.

    Returns:
        Tuple of (ScoutReport frontmatter, path to saved file).
    """
    identity = state.resolve_git_identity()
    today = date.today()

    note = ScoutReport(
        date=today,
        author=identity,
        repo_url=repo_url,
        repo_name=repo_name,
        dimensions=dimensions,
    )

    scout_path = _resolve_scout_path(project_dir, repo_name)
    vault.write_note(
        scout_path,
        note,
        sanitize.strip_analysis_blocks(content),
    )
    _update_state_body(project_dir, identity, repo_name)

    return note, scout_path


def load_scout(path: Path) -> tuple[ScoutReport, str]:
    """Read a scout report file.

    Takes absolute path (composable with list_scouts).

    Args:
        path: Absolute path to the scout report file.

    Returns:
        Tuple of (ScoutReport frontmatter, body text).

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    note = vault.read_note(path, ScoutReport)
    return note.frontmatter, note.body


def list_scouts(project_dir: Path) -> list[Path]:
    """All scout report paths, sorted oldest-first.

    Args:
        project_dir: Directory containing .mantle/.

    Returns:
        List of paths to scout report files. Empty if none.
    """
    scouts_dir = project.resolve_mantle_dir(project_dir) / "scouts"
    if not scouts_dir.is_dir():
        return []
    return sorted(scouts_dir.glob("*.md"))


# -- Internal helpers ---------------------------------------------


def _slugify(name: str) -> str:
    """Return a URL-safe slug, max 40 characters."""
    slug = name.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug[:40]


def _resolve_scout_path(project_dir: Path, repo_name: str) -> Path:
    """Compute non-colliding scout file path with auto-increment.

    Args:
        project_dir: Directory containing .mantle/.
        repo_name: Repository name used to generate filename slug.

    Returns:
        Path for the new scout report file.
    """
    scouts_dir = project.resolve_mantle_dir(project_dir) / "scouts"
    today = date.today().isoformat()
    slug = _slugify(repo_name)
    base = scouts_dir / f"{today}-{slug}.md"

    if not base.exists():
        return base

    counter = 2
    while True:
        path = scouts_dir / f"{today}-{slug}-{counter}.md"
        if not path.exists():
            return path
        counter += 1


def _update_state_body(
    project_dir: Path,
    identity: str,
    repo_name: str,
) -> None:
    """Update state.md body with scout report message.

    Overwrites Current Focus section content.

    Args:
        project_dir: Directory containing .mantle/.
        identity: Git email for the updated_by field.
        repo_name: Name of the scouted repository.
    """
    state_path = project.resolve_mantle_dir(project_dir) / "state.md"
    note = vault.read_note(state_path, state.ProjectState)

    message = (
        f"Scout report completed for {repo_name}"
        " — findings captured for planning.\n"
    )
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
