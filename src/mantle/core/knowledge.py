"""Distillation notes — synthesized knowledge from multiple sources."""

from __future__ import annotations

import re
from datetime import date
from typing import TYPE_CHECKING

import pydantic

from mantle.core import sanitize, state, vault

if TYPE_CHECKING:
    from pathlib import Path


# -- Data model ---------------------------------------------------


class DistillationNote(pydantic.BaseModel, frozen=True):
    """Distillation note frontmatter schema.

    Attributes:
        topic: The distillation subject.
        date: Date the distillation was saved.
        author: Git email of the author.
        source_count: Number of source notes synthesized.
        source_paths: Relative paths to source notes.
        tags: Mantle tags for categorization.
    """

    topic: str
    date: date
    author: str
    source_count: int
    source_paths: tuple[str, ...]
    tags: tuple[str, ...] = ("type/distillation",)


# -- Public API ---------------------------------------------------


def save_distillation(
    project_dir: Path,
    content: str,
    *,
    topic: str,
    source_paths: tuple[str, ...],
) -> tuple[DistillationNote, Path]:
    """Save content to .mantle/distillations/<date>-<slug>.md.

    Auto-increments filename on same-day same-slug collision
    (-2, -3, ...).

    Args:
        project_dir: Directory containing .mantle/.
        content: Distillation body content.
        topic: The distillation subject.
        source_paths: Relative paths to source notes.

    Returns:
        Tuple of (DistillationNote frontmatter, path to saved file).
    """
    identity = state.resolve_git_identity()
    today = date.today()

    note = DistillationNote(
        topic=topic,
        date=today,
        author=identity,
        source_count=len(source_paths),
        source_paths=source_paths,
    )

    distillation_path = _resolve_distillation_path(
        project_dir, topic
    )
    vault.write_note(
        distillation_path,
        note,
        sanitize.strip_analysis_blocks(content),
    )

    return note, distillation_path


def load_distillation(path: Path) -> tuple[DistillationNote, str]:
    """Read a distillation file.

    Takes absolute path (composable with list_distillations).

    Args:
        path: Absolute path to the distillation file.

    Returns:
        Tuple of (DistillationNote frontmatter, body text).

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    note = vault.read_note(path, DistillationNote)
    return note.frontmatter, note.body


def list_distillations(
    project_dir: Path,
    *,
    topic: str | None = None,
) -> list[Path]:
    """All distillation paths, sorted oldest-first.

    Args:
        project_dir: Directory containing .mantle/.
        topic: Optional topic filter (case-insensitive substring
            match).

    Returns:
        List of paths to distillation files. Empty if none.
    """
    distillations_dir = (
        project_dir / ".mantle" / "distillations"
    )
    if not distillations_dir.is_dir():
        return []
    paths = sorted(distillations_dir.glob("*.md"))
    if topic is None:
        return paths
    filtered = []
    for path in paths:
        note, _ = load_distillation(path)
        if topic.lower() in note.topic.lower():
            filtered.append(path)
    return filtered


def find_distillation_by_topic(
    project_dir: Path,
    topic: str,
) -> Path | None:
    """Return the most recent distillation matching topic.

    Uses exact match (case-insensitive).

    Args:
        project_dir: Directory containing .mantle/.
        topic: Topic to match (case-insensitive exact match).

    Returns:
        Path to the most recent matching distillation, or None.
    """
    distillations_dir = (
        project_dir / ".mantle" / "distillations"
    )
    if not distillations_dir.is_dir():
        return None
    paths = sorted(distillations_dir.glob("*.md"))
    matches = []
    for path in paths:
        note, _ = load_distillation(path)
        if note.topic.lower() == topic.lower():
            matches.append(path)
    if not matches:
        return None
    return matches[-1]


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


def _resolve_distillation_path(
    project_dir: Path, topic: str
) -> Path:
    """Compute non-colliding distillation file path.

    Auto-increments suffix on same-day same-slug collision
    (-2, -3, ...).

    Args:
        project_dir: Directory containing .mantle/.
        topic: Topic used to generate filename slug.

    Returns:
        Path for the new distillation file.
    """
    distillations_dir = (
        project_dir / ".mantle" / "distillations"
    )
    today = date.today().isoformat()
    slug = _slugify(topic)
    base = distillations_dir / f"{today}-{slug}.md"

    if not base.exists():
        return base

    counter = 2
    while True:
        path = (
            distillations_dir / f"{today}-{slug}-{counter}.md"
        )
        if not path.exists():
            return path
        counter += 1
