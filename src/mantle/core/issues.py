"""Issue planning — vertical slice issues with acceptance criteria."""

from __future__ import annotations

import re
from datetime import date
from typing import TYPE_CHECKING

import pydantic

from mantle.core import state, vault

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
        tags: Mantle tags for categorization.
    """

    title: str
    status: str = "planned"
    slice: tuple[str, ...]
    story_count: int = 0
    verification: str | None = None
    blocked_by: tuple[int, ...] = ()
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

    issue_path = _issue_path(project_dir, issue)

    if issue_path.exists() and not overwrite:
        raise IssueExistsError(issue_path)

    note = IssueNote(
        title=title,
        slice=slice,
        blocked_by=blocked_by,
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
    issues_dir = project_dir / ".mantle" / "issues"
    if not issues_dir.is_dir():
        return []
    return sorted(issues_dir.glob("issue-*.md"))


def next_issue_number(project_dir: Path) -> int:
    """Return the next issue number (highest existing + 1).

    Scans .mantle/issues/ for issue-NN.md files and returns max(NN) + 1.
    Returns 1 if no issues exist.

    Args:
        project_dir: Directory containing .mantle/.

    Returns:
        The next available issue number.
    """
    pattern = re.compile(r"issue-(\d+)\.md")
    highest = 0
    for path in list_issues(project_dir):
        match = pattern.match(path.name)
        if match:
            highest = max(highest, int(match.group(1)))
    return highest + 1


def issue_exists(project_dir: Path, issue: int) -> bool:
    """True if issue-NN.md exists.

    Args:
        project_dir: Directory containing .mantle/.
        issue: Issue number to check.

    Returns:
        True if the issue file exists.
    """
    return _issue_path(project_dir, issue).exists()


def count_issues(project_dir: Path) -> int:
    """Number of issue files.

    Args:
        project_dir: Directory containing .mantle/.

    Returns:
        Count of issue files.
    """
    return len(list_issues(project_dir))


_VERIFIED_FROM = frozenset({"implementing", "implemented"})


def transition_to_verified(project_root: Path, issue_number: int) -> Path:
    """Transition an issue to ``verified`` status.

    Loads the issue, validates the current status allows the
    transition (must be ``implementing`` or ``implemented``),
    updates status and tags, and writes back.

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
    issue_path = _issue_path(project_root, issue_number)
    note, body = load_issue(issue_path)

    if note.status not in _VERIFIED_FROM:
        raise InvalidTransitionError(note.status, "verified")

    # Replace status tag if present, otherwise append.
    new_tags = (
        *(t for t in note.tags if not t.startswith("status/")),
        "status/verified",
    )

    updated = note.model_copy(
        update={"status": "verified", "tags": new_tags},
    )
    vault.write_note(issue_path, updated, body)
    return issue_path


# ── Internal helpers ─────────────────────────────────────────────


def _issue_path(project_dir: Path, issue: int) -> Path:
    """Compute issue file path.

    Args:
        project_dir: Directory containing .mantle/.
        issue: Issue number.

    Returns:
        Path for the issue file.
    """
    return project_dir / ".mantle" / "issues" / f"issue-{issue:02d}.md"


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
    state_path = project_dir / ".mantle" / "state.md"
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
        r" — run /mantle:plan-issues for next issue"
        r" or /mantle:shape-issue to start shaping."
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
