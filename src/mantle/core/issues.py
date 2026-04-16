"""Issue planning — vertical slice issues with acceptance criteria."""

from __future__ import annotations

import re
from datetime import date
from typing import TYPE_CHECKING

import pydantic

from mantle.core import project, state, vault

if TYPE_CHECKING:
    from pathlib import Path


# ── Data model ───────────────────────────────────────────────────


class IssueNote(pydantic.BaseModel, frozen=True):
    """Issue frontmatter schema.

    Attributes:
        title: Short title for the issue.
        status: Issue lifecycle status.
        slice: Architectural layers this issue touches.
        story_count: Number of stories decomposed from this issue.
        verification: Optional per-issue verification override.
        blocked_by: Issue numbers this issue depends on.
        skills_required: Skills needed for this issue.
        tags: Mantle tags for categorization.
    """

    title: str
    status: str = "planned"
    slice: tuple[str, ...]
    story_count: int = 0
    verification: str | None = None
    blocked_by: tuple[int, ...] = ()
    skills_required: tuple[str, ...] = ()
    tags: tuple[str, ...] = ("type/issue", "status/planned")


# ── Exception ────────────────────────────────────────────────────


class IssueExistsError(Exception):
    """Raised when an issue file already exists at the target path.

    Attributes:
        path: Path to the existing issue file.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        super().__init__(f"Issue already exists at {path}")


class InvalidTransitionError(Exception):
    """Raised when a status transition is not allowed.

    Attributes:
        current_status: The current issue status.
        target_status: The target status that was rejected.
    """

    def __init__(self, current_status: str, target_status: str) -> None:
        self.current_status = current_status
        self.target_status = target_status
        super().__init__(
            f"Cannot transition from '{current_status}' to '{target_status}'"
        )


# ── Public API ───────────────────────────────────────────────────


def save_issue(
    project_dir: Path,
    content: str,
    *,
    title: str,
    slice: tuple[str, ...],
    blocked_by: tuple[int, ...] = (),
    skills_required: tuple[str, ...] = (),
    verification: str | None = None,
    issue: int | None = None,
    overwrite: bool = False,
) -> tuple[IssueNote, Path]:
    """Save issue to .mantle/issues/issue-NN.md.

    Auto-assigns the next issue number unless ``issue`` is provided.
    Raises if file exists and ``overwrite`` is False. Updates state.md
    Current Focus and transitions to PLANNING if needed.

    Args:
        project_dir: Directory containing .mantle/.
        content: Full issue body (markdown).
        title: Short title for the issue.
        slice: Architectural layers this issue touches.
        blocked_by: Issue numbers this issue depends on.
        skills_required: Skills needed for this issue.
        verification: Optional per-issue verification override.
        issue: Explicit issue number (for overwrites). Auto-assigns when None.
        overwrite: Replace existing issue file.

    Returns:
        Tuple of (IssueNote frontmatter, path to saved file).

    Raises:
        IssueExistsError: If file exists and overwrite is False.
    """
    if issue is None:
        issue = next_issue_number(project_dir)

    # Check for existing issue with this number (any slug)
    existing = find_issue_path(project_dir, issue)
    if existing is not None and not overwrite:
        raise IssueExistsError(existing)

    issue_path = _issue_path(project_dir, issue, title)

    note = IssueNote(
        title=title,
        slice=slice,
        blocked_by=blocked_by,
        skills_required=skills_required,
        verification=verification,
    )

    vault.write_note(issue_path, note, content)

    identity = state.resolve_git_identity()
    _update_state_body(project_dir, identity, issue)

    return note, issue_path


def load_issue(path: Path) -> tuple[IssueNote, str]:
    """Read an issue file.

    Takes absolute path (composable with list_issues).

    Args:
        path: Absolute path to the issue file.

    Returns:
        Tuple of (IssueNote frontmatter, body text).

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    note = vault.read_note(path, IssueNote)
    return note.frontmatter, note.body


def list_issues(project_dir: Path) -> list[Path]:
    """All issue paths in .mantle/issues/, sorted oldest-first.

    Args:
        project_dir: Directory containing .mantle/.

    Returns:
        List of paths to issue files. Empty if none.
    """
    issues_dir = project.resolve_mantle_dir(project_dir) / "issues"
    if not issues_dir.is_dir():
        return []
    return sorted(issues_dir.glob("issue-*.md"))


def list_archived_issues(project_dir: Path) -> list[Path]:
    """All issue paths in .mantle/archive/issues/, sorted oldest-first.

    Args:
        project_dir: Directory containing .mantle/.

    Returns:
        List of paths to archived issue files. Empty if the archive
        directory does not exist.
    """
    archive_dir = project.resolve_mantle_dir(project_dir) / "archive" / "issues"
    if not archive_dir.is_dir():
        return []
    return sorted(archive_dir.glob("issue-*.md"))


def next_issue_number(project_dir: Path) -> int:
    """Return the next issue number (highest existing + 1).

    Scans both .mantle/issues/ and .mantle/archive/issues/ for issue-NN.md
    files and returns max(NN) + 1. Returns 1 if no issues exist in either
    location. The archive scan is skipped silently if the archive directory
    does not exist.

    Args:
        project_dir: Directory containing .mantle/.

    Returns:
        The next available issue number.
    """
    pattern = re.compile(r"issue-(\d+)-.*\.md")
    highest = 0
    for path in list_issues(project_dir):
        match = pattern.match(path.name)
        if match:
            highest = max(highest, int(match.group(1)))
    archive_dir = project.resolve_mantle_dir(project_dir) / "archive" / "issues"
    if archive_dir.is_dir():
        for path in archive_dir.glob("issue-*.md"):
            match = pattern.match(path.name)
            if match:
                highest = max(highest, int(match.group(1)))
    return highest + 1


def issue_exists(project_dir: Path, issue: int) -> bool:
    """True if an issue file exists for the given number.

    Args:
        project_dir: Directory containing .mantle/.
        issue: Issue number to check.

    Returns:
        True if the issue file exists.
    """
    return find_issue_path(project_dir, issue) is not None


def count_issues(project_dir: Path) -> int:
    """Number of issue files.

    Args:
        project_dir: Directory containing .mantle/.

    Returns:
        Count of issue files.
    """
    return len(list_issues(project_dir))


_ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    "verified": frozenset({"implementing", "implemented"}),
    "approved": frozenset({"verified"}),
    "implementing": frozenset(
        {"planned", "verified", "implementing", "implemented"}
    ),
    "implemented": frozenset({"implementing"}),
}


def _transition_issue(
    project_root: Path,
    issue_number: int,
    target_status: str,
) -> Path:
    """Transition an issue to a new status.

    Loads the issue, validates the current status against
    ``_ALLOWED_TRANSITIONS``, updates status and tags, and
    writes back.

    Args:
        project_root: Directory containing .mantle/.
        issue_number: Issue number to transition.
        target_status: The status to transition to.

    Returns:
        Path to the updated issue file.

    Raises:
        InvalidTransitionError: If current status does not allow
            the transition.
        FileNotFoundError: If the issue file does not exist.
    """
    allowed_from = _ALLOWED_TRANSITIONS[target_status]
    issue_path = find_issue_path(project_root, issue_number)
    if issue_path is None:
        msg = f"Issue {issue_number} not found"
        raise FileNotFoundError(msg)
    note, body = load_issue(issue_path)

    if note.status not in allowed_from:
        raise InvalidTransitionError(note.status, target_status)

    new_tags = (
        *(t for t in note.tags if not t.startswith("status/")),
        f"status/{target_status}",
    )

    updated = note.model_copy(
        update={"status": target_status, "tags": new_tags},
    )
    vault.write_note(issue_path, updated, body)
    return issue_path


def transition_to_verified(project_root: Path, issue_number: int) -> Path:
    """Transition an issue to ``verified`` status.

    Args:
        project_root: Directory containing .mantle/.
        issue_number: Issue number to transition.

    Returns:
        Path to the updated issue file.

    Raises:
        InvalidTransitionError: If current status does not allow
            transition to ``verified``.
        FileNotFoundError: If the issue file does not exist.
    """
    return _transition_issue(project_root, issue_number, "verified")


def transition_to_approved(project_root: Path, issue_number: int) -> Path:
    """Transition an issue to ``approved`` status.

    Args:
        project_root: Directory containing .mantle/.
        issue_number: Issue number to transition.

    Returns:
        Path to the updated issue file.

    Raises:
        InvalidTransitionError: If current status does not allow
            transition to ``approved``.
        FileNotFoundError: If the issue file does not exist.
    """
    return _transition_issue(project_root, issue_number, "approved")


def transition_to_implementing(
    project_root: Path,
    issue_number: int,
) -> Path:
    """Transition an issue to ``implementing`` status.

    Args:
        project_root: Directory containing .mantle/.
        issue_number: Issue number to transition.

    Returns:
        Path to the updated issue file.

    Raises:
        InvalidTransitionError: If current status does not allow
            transition to ``implementing``.
        FileNotFoundError: If the issue file does not exist.
    """
    return _transition_issue(project_root, issue_number, "implementing")


def transition_to_implemented(
    project_root: Path,
    issue_number: int,
) -> Path:
    """Transition an issue to ``implemented`` status.

    Args:
        project_root: Directory containing .mantle/.
        issue_number: Issue number to transition.

    Returns:
        Path to the updated issue file.

    Raises:
        InvalidTransitionError: If current status does not allow
            transition to ``implemented``.
        FileNotFoundError: If the issue file does not exist.
    """
    return _transition_issue(project_root, issue_number, "implemented")


# ── Internal helpers ─────────────────────────────────────────────


def _slugify_title(title: str) -> str:
    """Convert a title to a filename-safe slug.

    Lowercase, replace spaces with hyphens, strip non-alphanumeric
    characters (except hyphens), truncate to 30 chars.

    Args:
        title: Human-readable title.

    Returns:
        Lowercased, hyphenated slug.
    """
    slug = title.lower().replace(" ", "-")
    slug = re.sub(r"[^a-z0-9-]", "", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug[:30].rstrip("-")


def _issue_path(project_dir: Path, issue: int, title: str) -> Path:
    """Compute issue file path with slug.

    Args:
        project_dir: Directory containing .mantle/.
        issue: Issue number.
        title: Issue title (slugified for filename).

    Returns:
        Path for the issue file.
    """
    slug = _slugify_title(title)
    mantle_dir = project.resolve_mantle_dir(project_dir)
    return mantle_dir / "issues" / f"issue-{issue:02d}-{slug}.md"


def find_issue_path(project_dir: Path, issue: int) -> Path | None:
    """Find an issue file by number using glob lookup.

    Args:
        project_dir: Directory containing .mantle/.
        issue: Issue number.

    Returns:
        Path to the issue file, or None if not found.
    """
    issues_dir = project.resolve_mantle_dir(project_dir) / "issues"
    matches = sorted(issues_dir.glob(f"issue-{issue:02d}-*.md"))
    if matches:
        return matches[0]
    # Fallback: old naming format without slug (issue-NN.md)
    old_format = issues_dir / f"issue-{issue:02d}.md"
    return old_format if old_format.exists() else None


def _update_state_body(
    project_dir: Path,
    identity: str,
    issue: int,
) -> None:
    """Update state.md Current Focus and transition to PLANNING if needed.

    Args:
        project_dir: Directory containing .mantle/.
        identity: Git email for the updated_by field.
        issue: Issue number that was planned.
    """
    state_path = project.resolve_mantle_dir(project_dir) / "state.md"
    note = vault.read_note(state_path, state.ProjectState)

    current_status = note.frontmatter.status
    if current_status in (state.Status.SYSTEM_DESIGN, state.Status.ADOPTED):
        state.transition(project_dir, state.Status.PLANNING)
        # Re-read after transition to get updated frontmatter
        note = vault.read_note(state_path, state.ProjectState)
    elif current_status != state.Status.PLANNING:
        allowed = state.valid_transitions(current_status)
        raise state.InvalidTransitionError(
            current_status, state.Status.PLANNING, allowed
        )

    body = re.sub(
        r"(## Current Focus\n\n).*?(?=\n##|\Z)",
        rf"\1Issue {issue} planned"
        r" — run /mantle:build to automate the full pipeline,"
        r" /mantle:shape-issue for manual control,"
        r" or /mantle:plan-issues for next issue."
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
