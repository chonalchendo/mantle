"""Research notes — validate ideas with evidence from web research."""

from __future__ import annotations

import re
from datetime import date
from typing import TYPE_CHECKING

import pydantic

from mantle.core import issues, project, sanitize, state, vault

if TYPE_CHECKING:
    from pathlib import Path


# ── Data model ───────────────────────────────────────────────────


VALID_FOCUSES: frozenset[str] = frozenset(
    {
        "general",
        "feasibility",
        "competitive",
        "technology",
        "user-needs",
    }
)


class ResearchNote(pydantic.BaseModel, frozen=True):
    """Research note frontmatter schema.

    Attributes:
        date: Date the research was saved.
        author: Git email of the researcher.
        focus: Research angle (one of VALID_FOCUSES).
        confidence: Confidence rating as "N/10" string.
        idea_ref: Snapshot of the idea's problem field.
        tags: Mantle tags for categorization.
    """

    date: date
    author: str
    focus: str
    confidence: str
    idea_ref: str
    tags: tuple[str, ...] = ("type/research", "phase/research")


# ── Exception ────────────────────────────────────────────────────


class IdeaNotFoundError(Exception):
    """Raised when save_research is called without idea.md.

    Attributes:
        path: Expected path to idea.md.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        super().__init__(f"No idea.md found at {path}")


class IssueNotFoundError(Exception):
    """Raised when save_research is called with an unknown issue number.

    Attributes:
        issue: The issue number that could not be resolved.
    """

    def __init__(self, issue: int) -> None:
        self.issue = issue
        super().__init__(f"No issue file found for issue {issue}")


# ── Public API ───────────────────────────────────────────────────


def save_research(
    project_dir: Path,
    content: str,
    *,
    focus: str,
    confidence: str,
    update_state: bool = True,
    issue: int | None = None,
) -> tuple[ResearchNote, Path]:
    """Save content to .mantle/research/.

    In idea mode (default), the filename is ``<date>-<focus>.md`` and
    ``idea_ref`` is snapshotted from ``idea.md``. In issue mode
    (``issue`` given), the filename is ``issue-<NN>-<focus>.md`` and
    ``idea_ref`` is snapshotted from the issue title; ``idea.md`` is
    not required. Auto-increments filename on collision (-2, -3, ...).

    Args:
        project_dir: Directory containing .mantle/.
        content: Research note body content.
        focus: Research angle (must be in VALID_FOCUSES).
        confidence: Confidence rating in "N/10" format.
        update_state: Whether to update state.md Current Focus.
            Set to False when research is a sub-step of another
            command (e.g. /mantle:add-skill). Ignored in issue mode.
        issue: If given, save in issue mode — load the issue file
            for the ``idea_ref`` snapshot and name the file
            ``issue-<NN>-<focus>.md``. Skips the ``idea.md`` check.

    Returns:
        Tuple of (ResearchNote frontmatter, path to saved file).

    Raises:
        IdeaNotFoundError: Idea mode only — if idea.md does not exist.
        IssueNotFoundError: Issue mode only — if the issue file does
            not exist.
        ValueError: If focus is invalid or confidence format is wrong.
    """
    if focus not in VALID_FOCUSES:
        msg = (
            f"Invalid focus '{focus}'. "
            f"Must be one of: {', '.join(sorted(VALID_FOCUSES))}"
        )
        raise ValueError(msg)

    if not re.fullmatch(r"\d{1,2}/10", confidence):
        msg = (
            f"Invalid confidence '{confidence}'. "
            f"Must be in N/10 format (e.g. '7/10')"
        )
        raise ValueError(msg)

    mantle_dir = project.resolve_mantle_dir(project_dir)

    if issue is not None:
        idea_ref = _load_issue_idea_ref(project_dir, issue)
    else:
        idea_path = mantle_dir / "idea.md"
        if not idea_path.exists():
            raise IdeaNotFoundError(idea_path)
        from mantle.core import idea

        idea_ref = idea.load_idea(project_dir).problem

    identity = state.resolve_git_identity()
    today = date.today()

    note = ResearchNote(
        date=today,
        author=identity,
        focus=focus,
        confidence=confidence,
        idea_ref=idea_ref,
    )

    research_path = _resolve_research_path(project_dir, focus, issue=issue)
    vault.write_note(
        research_path, note, sanitize.strip_analysis_blocks(content)
    )
    if update_state and issue is None:
        _update_state_body(project_dir, identity, focus)

    return note, research_path


def _load_issue_idea_ref(project_dir: Path, issue: int) -> str:
    """Return the issue title as the ``idea_ref`` for issue-mode research.

    Looks in live `.mantle/issues/` and then `.mantle/archive/issues/`.

    Args:
        project_dir: Directory containing .mantle/.
        issue: Issue number.

    Returns:
        The issue title string.

    Raises:
        IssueNotFoundError: If no issue file can be found.
    """
    path = issues.find_issue_path(project_dir, issue)
    if path is None:
        raise IssueNotFoundError(issue)
    note, _ = issues.load_issue(path)
    return note.title


def load_research(path: Path) -> tuple[ResearchNote, str]:
    """Read a research file.

    Takes absolute path (composable with list_research).

    Args:
        path: Absolute path to the research file.

    Returns:
        Tuple of (ResearchNote frontmatter, body text).

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    note = vault.read_note(path, ResearchNote)
    return note.frontmatter, note.body


def list_research(project_dir: Path) -> list[Path]:
    """All research paths, sorted oldest-first.

    Args:
        project_dir: Directory containing .mantle/.

    Returns:
        List of paths to research files. Empty if none.
    """
    research_dir = project.resolve_mantle_dir(project_dir) / "research"
    if not research_dir.is_dir():
        return []
    return sorted(research_dir.glob("*.md"))


def research_exists(project_dir: Path) -> bool:
    """True if at least one research note exists.

    Args:
        project_dir: Directory containing .mantle/.

    Returns:
        True if any research files exist.
    """
    return len(list_research(project_dir)) > 0


# ── Internal helpers ─────────────────────────────────────────────


def _resolve_research_path(
    project_dir: Path,
    focus: str,
    *,
    issue: int | None = None,
) -> Path:
    """Compute non-colliding research file path with auto-increment.

    Args:
        project_dir: Directory containing .mantle/.
        focus: Research focus angle for the filename.
        issue: If given, use ``issue-<NN>-<focus>.md`` naming.

    Returns:
        Path for the new research file.
    """
    research_dir = project.resolve_mantle_dir(project_dir) / "research"
    research_dir.mkdir(parents=True, exist_ok=True)
    if issue is not None:
        stem = f"issue-{issue:02d}-{focus}"
    else:
        stem = f"{date.today().isoformat()}-{focus}"
    base = research_dir / f"{stem}.md"

    if not base.exists():
        return base

    counter = 2
    while True:
        path = research_dir / f"{stem}-{counter}.md"
        if not path.exists():
            return path
        counter += 1


def _update_state_body(
    project_dir: Path,
    identity: str,
    focus: str,
) -> None:
    """Update state.md body with research summary and refresh timestamps.

    Overwrites Current Focus section content (not fragile placeholder
    search).

    Args:
        project_dir: Directory containing .mantle/.
        identity: Git email for the updated_by field.
        focus: Research focus angle for the message.
    """
    state_path = project.resolve_mantle_dir(project_dir) / "state.md"
    note = vault.read_note(state_path, state.ProjectState)

    body = re.sub(
        r"(## Current Focus\n\n).*?(?=\n##|\Z)",
        (
            rf"\1Research ({focus}) completed"
            r" — run /mantle:research for another angle"
            r" or /mantle:design-product next."
            "\n"
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
