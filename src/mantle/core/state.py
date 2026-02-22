"""Project state management with state machine validation."""

from __future__ import annotations

import enum
import subprocess
from datetime import date
from typing import TYPE_CHECKING

import pydantic

from mantle.core import vault

if TYPE_CHECKING:
    from pathlib import Path


# ── Data model ───────────────────────────────────────────────────


class Status(enum.Enum):
    """Project lifecycle status."""

    IDEA = "idea"
    CHALLENGE = "challenge"
    PRODUCT_DESIGN = "product-design"
    SYSTEM_DESIGN = "system-design"
    PLANNING = "planning"
    IMPLEMENTING = "implementing"
    VERIFYING = "verifying"
    REVIEWING = "reviewing"
    COMPLETED = "completed"


class ProjectState(pydantic.BaseModel, frozen=True):
    """State.md frontmatter schema.

    Attributes:
        project: Project name derived from directory.
        status: Current lifecycle status.
        confidence: Confidence rating as "N/10" string.
        created: Date the project was initialized.
        created_by: Git email of the creator.
        updated: Date of the last state change.
        updated_by: Git email of the last updater.
        current_issue: Active issue number, if any.
        current_story: Active story number, if any.
        skills_required: Skills needed for current work.
        tags: Mantle tags for categorization.
    """

    project: str
    status: Status
    confidence: str = "0/10"
    created: date
    created_by: str
    updated: date
    updated_by: str
    current_issue: int | None = None
    current_story: int | None = None
    skills_required: tuple[str, ...] = ()
    tags: tuple[str, ...] = ("status/active",)


# ── Transition map ───────────────────────────────────────────────


_TRANSITIONS: dict[Status, frozenset[Status]] = {
    Status.IDEA: frozenset({Status.CHALLENGE, Status.PRODUCT_DESIGN}),
    Status.CHALLENGE: frozenset({Status.PRODUCT_DESIGN}),
    Status.PRODUCT_DESIGN: frozenset({Status.SYSTEM_DESIGN}),
    Status.SYSTEM_DESIGN: frozenset({Status.PLANNING}),
    Status.PLANNING: frozenset({Status.IMPLEMENTING}),
    Status.IMPLEMENTING: frozenset({Status.VERIFYING, Status.PLANNING}),
    Status.VERIFYING: frozenset({Status.REVIEWING, Status.IMPLEMENTING}),
    Status.REVIEWING: frozenset({Status.COMPLETED, Status.IMPLEMENTING}),
    Status.COMPLETED: frozenset(),
}


# ── Exception ────────────────────────────────────────────────────


class InvalidTransitionError(Exception):
    """Raised when a state transition is not allowed.

    Attributes:
        current: The status being transitioned from.
        target: The requested target status.
        valid_targets: Statuses that are valid from current.
    """

    def __init__(
        self,
        current: Status,
        target: Status,
        valid_targets: frozenset[Status],
    ) -> None:
        self.current = current
        self.target = target
        self.valid_targets = valid_targets
        super().__init__(str(self))

    def __str__(self) -> str:
        targets = ", ".join(
            sorted(s.value for s in self.valid_targets)
        )
        if targets:
            return (
                f"Cannot transition from '{self.current.value}' "
                f"to '{self.target.value}'. "
                f"Valid targets: {targets}"
            )
        return (
            f"Cannot transition from '{self.current.value}' "
            f"to '{self.target.value}'. "
            f"No transitions allowed (terminal state)"
        )


# ── State body template ─────────────────────────────────────────

_INITIAL_BODY = """\
## Summary

_Describe the project in one or two sentences._

## Current Focus

_What are you working on right now?_

## Blockers

_Anything preventing progress?_

## Recent Decisions

_Key decisions made recently._

## Next Steps

_What comes next?_
"""


# ── Public API ───────────────────────────────────────────────────


def create_initial_state(
    project_dir: Path,
    project_name: str,
) -> ProjectState:
    """Create state.md with initial project state.

    Args:
        project_dir: Directory containing .mantle/.
        project_name: Name for the project.

    Returns:
        The created ProjectState.
    """
    identity = resolve_git_identity()
    today = date.today()

    state = ProjectState(
        project=project_name,
        status=Status.IDEA,
        created=today,
        created_by=identity,
        updated=today,
        updated_by=identity,
    )

    path = project_dir / ".mantle" / "state.md"
    vault.write_note(path, state, _INITIAL_BODY)
    return state


def load_state(project_dir: Path) -> ProjectState:
    """Read state.md and return the project state.

    Args:
        project_dir: Directory containing .mantle/.

    Returns:
        The current ProjectState.

    Raises:
        FileNotFoundError: If state.md does not exist.
    """
    path = project_dir / ".mantle" / "state.md"
    note = vault.read_note(path, ProjectState)
    return note.frontmatter


def transition(project_dir: Path, target: Status) -> ProjectState:
    """Transition the project to a new status.

    Args:
        project_dir: Directory containing .mantle/.
        target: The status to transition to.

    Returns:
        The updated ProjectState.

    Raises:
        InvalidTransitionError: If the transition is not allowed.
    """
    path = project_dir / ".mantle" / "state.md"
    note = vault.read_note(path, ProjectState)
    current = note.frontmatter

    allowed = valid_transitions(current.status)
    if target not in allowed:
        raise InvalidTransitionError(current.status, target, allowed)

    identity = resolve_git_identity()
    updated = current.model_copy(
        update={
            "status": target,
            "updated": date.today(),
            "updated_by": identity,
        },
    )

    vault.write_note(path, updated, note.body)
    return updated


def update_tracking(
    project_dir: Path,
    *,
    current_issue: int | None = None,
    current_story: int | None = None,
) -> ProjectState:
    """Update tracking fields without changing status.

    Args:
        project_dir: Directory containing .mantle/.
        current_issue: Issue number to track (or None to clear).
        current_story: Story number to track (or None to clear).

    Returns:
        The updated ProjectState.
    """
    path = project_dir / ".mantle" / "state.md"
    note = vault.read_note(path, ProjectState)
    current = note.frontmatter

    identity = resolve_git_identity()
    updated = current.model_copy(
        update={
            "current_issue": current_issue,
            "current_story": current_story,
            "updated": date.today(),
            "updated_by": identity,
        },
    )

    vault.write_note(path, updated, note.body)
    return updated


def valid_transitions(status: Status) -> frozenset[Status]:
    """Return the set of valid target statuses for a given status.

    Args:
        status: The current status.

    Returns:
        Frozenset of valid target statuses.
    """
    return _TRANSITIONS[status]


def resolve_git_identity() -> str:
    """Resolve the current git user identity.

    Returns:
        The git user email.

    Raises:
        RuntimeError: If git is not configured or not available.
    """
    result = subprocess.run(
        ["git", "config", "user.email"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        msg = (
            "Could not resolve git identity. "
            "Run 'git config user.email' to configure."
        )
        raise RuntimeError(msg)
    return result.stdout.strip()
