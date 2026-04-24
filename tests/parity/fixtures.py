"""Deterministic sandbox fixture factory for parity tests."""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from mantle.core import issues, session, state, vault

if TYPE_CHECKING:
    from pathlib import Path


def build_sandbox_fixture(tmp_path: Path) -> Path:
    """Create a minimal, deterministic .mantle/ tree.

    Named scenario fixture: "sandbox with one planned issue and a static
    session".

    Writes:

    - ``.mantle/state.md`` — frontmatter with ``project="sandbox"``,
      ``status="planning"``, and stable created/updated dates.
    - ``.mantle/issues/issue-01-example.md`` — a single planned issue
      with 2 acceptance criteria stubs.
    - ``.mantle/sessions/2026-01-01-session.md`` — one stable session
      file.

    Args:
        tmp_path: Root directory for the sandbox project.

    Returns:
        ``tmp_path`` (the project root containing ``.mantle/``).
    """
    mantle_dir = tmp_path / ".mantle"
    mantle_dir.mkdir(parents=True, exist_ok=True)
    (mantle_dir / "issues").mkdir(parents=True, exist_ok=True)
    (mantle_dir / "sessions").mkdir(parents=True, exist_ok=True)

    _write_state(tmp_path)
    _write_issue(tmp_path)
    _write_session(tmp_path)

    return tmp_path


# ── Internal helpers ─────────────────────────────────────────────


def _write_state(project_dir: Path) -> None:
    """Write a deterministic state.md in planning status."""
    stable_date = date(2026, 1, 1)
    project_state = state.ProjectState(
        project="sandbox",
        status=state.Status.PLANNING,
        confidence="5/10",
        created=stable_date,
        created_by="sandbox@example.com",
        updated=stable_date,
        updated_by="sandbox@example.com",
    )
    body = (
        "## Summary\n\n"
        "A deterministic sandbox project for parity testing.\n\n"
        "## Current Focus\n\n"
        "Issue 01 planned — run /mantle:build to begin.\n\n"
        "## Blockers\n\n"
        "None.\n\n"
        "## Recent Decisions\n\n"
        "Chose minimal scope for sandbox.\n\n"
        "## Next Steps\n\n"
        "Implement issue 01.\n"
    )
    path = project_dir / ".mantle" / "state.md"
    vault.write_note(path, project_state, body)


def _write_issue(project_dir: Path) -> None:
    """Write a single planned issue with 2 AC stubs."""
    note = issues.IssueNote(
        title="Example issue",
        status="planned",
        slice=("core",),
        story_count=0,
        tags=("type/issue", "status/planned"),
    )
    body = (
        "## Why\n\n"
        "A deterministic example issue for parity tests.\n\n"
        "## Acceptance Criteria\n\n"
        "- [ ] ac-01: First criterion.\n"
        "- [ ] ac-02: Second criterion.\n"
    )
    path = project_dir / ".mantle" / "issues" / "issue-01-example.md"
    vault.write_note(path, note, body)


def _write_session(project_dir: Path) -> None:
    """Write a stable session file."""
    note = session.SessionNote(
        project="sandbox",
        author="sandbox@example.com",
        date=datetime(2026, 1, 1, 9, 0),
        commands_used=("build",),
    )
    body = (
        "## Summary\n\n"
        "Initialized sandbox project.\n\n"
        "## What Was Done\n\n"
        "- Created initial structure.\n\n"
        "## Decisions Made\n\n"
        "None.\n\n"
        "## What's Next\n\n"
        "Implement issue 01.\n\n"
        "## Open Questions\n\n"
        "None.\n"
    )
    path = project_dir / ".mantle" / "sessions" / "2026-01-01-session.md"
    vault.write_note(path, note, body)
