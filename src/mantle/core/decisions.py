"""Decision log — structured decision records with rationale."""

from __future__ import annotations

import re
from datetime import date
from typing import TYPE_CHECKING

import pydantic

from mantle.core import project, state, vault

if TYPE_CHECKING:
    from pathlib import Path


# ── Data model ───────────────────────────────────────────────────


class DecisionNote(pydantic.BaseModel, frozen=True):
    """Decision file frontmatter schema.

    Attributes:
        date: Date the decision was recorded.
        author: Git email of the decision author.
        topic: Slug used in filename.
        scope: Area this decision applies to.
        confidence: Confidence rating as "N/10" string.
        reversible: How easily this decision can be reversed.
        tags: Mantle tags for categorization.
    """

    date: date
    author: str
    topic: str
    scope: str
    confidence: str
    reversible: str
    tags: tuple[str, ...] = (
        "type/decision",
        "phase/system-design",
    )


# ── Public API ───────────────────────────────────────────────────


def save_decision(
    project_dir: Path,
    *,
    topic: str,
    decision: str,
    alternatives: list[str],
    rationale: str,
    reversal_trigger: str,
    confidence: str,
    reversible: str,
    scope: str,
) -> tuple[DecisionNote, Path]:
    """Save a decision to .mantle/decisions/<date>-<topic>.md.

    Auto-increments filename on same-day/same-topic collision.

    Args:
        project_dir: Directory containing .mantle/.
        topic: Decision topic (slugified for filename).
        decision: The decision text.
        alternatives: Alternatives that were considered.
        rationale: Why this option was chosen.
        reversal_trigger: What would change this decision.
        confidence: Confidence rating as "N/10".
        reversible: Reversibility (high / medium / low).
        scope: Decision scope.

    Returns:
        Tuple of (DecisionNote frontmatter, path to saved file).
    """
    identity = state.resolve_git_identity()
    today = date.today()
    slug = _slugify(topic)

    note = DecisionNote(
        date=today,
        author=identity,
        topic=slug,
        scope=scope,
        confidence=confidence,
        reversible=reversible,
    )

    body = _build_body(
        decision=decision,
        alternatives=alternatives,
        rationale=rationale,
        reversal_trigger=reversal_trigger,
    )

    path = _resolve_decision_path(project_dir, slug)
    vault.write_note(path, note, body)

    return note, path


def load_decision(path: Path) -> tuple[DecisionNote, str]:
    """Read a decision file.

    Takes absolute path (composable with list_decisions).

    Args:
        path: Absolute path to the decision file.

    Returns:
        Tuple of (DecisionNote frontmatter, body text).

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    note = vault.read_note(path, DecisionNote)
    return note.frontmatter, note.body


def list_decisions(project_dir: Path) -> list[Path]:
    """All decision paths, sorted oldest-first.

    Args:
        project_dir: Directory containing .mantle/.

    Returns:
        List of paths to decision files. Empty if none.
    """
    decisions_dir = project.resolve_mantle_dir(project_dir) / "decisions"
    if not decisions_dir.is_dir():
        return []
    return sorted(decisions_dir.glob("*.md"))


def decision_exists(project_dir: Path) -> bool:
    """True if at least one decision file exists.

    Args:
        project_dir: Directory containing .mantle/.

    Returns:
        True if any decision files exist.
    """
    return len(list_decisions(project_dir)) > 0


# ── Internal helpers ─────────────────────────────────────────────


def _slugify(text: str) -> str:
    """Convert text to a URL-friendly slug.

    Args:
        text: Text to slugify.

    Returns:
        Lowercased, hyphenated slug.
    """
    slug = text.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


def _build_body(
    *,
    decision: str,
    alternatives: list[str],
    rationale: str,
    reversal_trigger: str,
) -> str:
    """Build markdown body from structured decision inputs.

    Args:
        decision: The decision text.
        alternatives: Alternatives considered.
        rationale: Why this was chosen.
        reversal_trigger: What would change this decision.

    Returns:
        Formatted markdown body string.
    """
    alt_list = "\n".join(f"- {a}" for a in alternatives)
    return (
        f"## Decision\n\n{decision}\n\n"
        f"## Alternatives Considered\n\n{alt_list}\n\n"
        f"## Rationale\n\n{rationale}\n\n"
        f"## Reversal Trigger\n\n{reversal_trigger}\n"
    )


def _resolve_decision_path(
    project_dir: Path,
    slug: str,
) -> Path:
    """Compute non-colliding decision file path with auto-increment.

    Args:
        project_dir: Directory containing .mantle/.
        slug: Slugified topic for filename.

    Returns:
        Path for the new decision file.
    """
    decisions_dir = project.resolve_mantle_dir(project_dir) / "decisions"
    today = date.today().isoformat()
    base = decisions_dir / f"{today}-{slug}.md"

    if not base.exists():
        return base

    counter = 2
    while True:
        path = decisions_dir / f"{today}-{slug}-{counter}.md"
        if not path.exists():
            return path
        counter += 1
