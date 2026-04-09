"""Tests for mantle.core.issues."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING
from unittest.mock import patch

import pydantic
import pytest

if TYPE_CHECKING:
    from pathlib import Path

from mantle.core import issues as issues_mod
from mantle.core import vault
from mantle.core.issues import (
    InvalidTransitionError,
    IssueExistsError,
    IssueNote,
    count_issues,
    issue_exists,
    list_issues,
    load_issue,
    next_issue_number,
    save_issue,
)
from mantle.core.state import ProjectState, Status

MOCK_EMAIL = "test@example.com"
CONTENT = (
    "## Parent PRD\n\n"
    "product-design.md, system-design.md\n\n"
    "## What to build\n\n"
    "Build the thing.\n\n"
    "## Acceptance criteria\n\n"
    "- [ ] It works\n"
)


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """Create a minimal .mantle/ with state.md and issues dir."""
    (tmp_path / ".mantle").mkdir()
    (tmp_path / ".mantle" / "issues").mkdir()
    _write_state(tmp_path)
    return tmp_path


def _mock_git_identity() -> str:
    return MOCK_EMAIL


def _write_state(
    project_dir: Path,
    *,
    status: Status = Status.SYSTEM_DESIGN,
    body: str | None = None,
) -> None:
    """Write a state.md for testing."""
    st = ProjectState(
        project="test-project",
        status=status,
        confidence="5/10",
        created=date(2025, 1, 1),
        created_by=MOCK_EMAIL,
        updated=date(2025, 1, 1),
        updated_by=MOCK_EMAIL,
    )
    if body is None:
        body = (
            "## Summary\n\n"
            "Test project\n\n"
            "## Current Focus\n\n"
            "Designing the system.\n\n"
            "## Blockers\n\n"
            "_Anything preventing progress?_\n"
        )
    path = project_dir / ".mantle" / "state.md"
    vault.write_note(path, st, body)


def _save(
    project_dir: Path,
    *,
    title: str = "Context compilation engine",
    slice: tuple[str, ...] = ("core", "tests"),
    content: str = CONTENT,
    blocked_by: tuple[int, ...] = (),
    verification: str | None = None,
    issue: int | None = None,
    overwrite: bool = False,
) -> tuple[IssueNote, Path]:
    """Save an issue with sensible defaults."""
    return save_issue(
        project_dir,
        content,
        title=title,
        slice=slice,
        blocked_by=blocked_by,
        verification=verification,
        issue=issue,
        overwrite=overwrite,
    )


def _create_archived_issue(
    project_dir: Path, number: int, slug: str = "archived-work"
) -> None:
    """Create a fake archived issue file directly for test setup."""
    archive_dir = project_dir / ".mantle" / "archive" / "issues"
    archive_dir.mkdir(parents=True, exist_ok=True)
    (archive_dir / f"issue-{number:02d}-{slug}.md").write_text(
        "---\ntitle: x\n---\n"
    )


# ── IssueNote model ─────────────────────────────────────────────


class TestIssueNote:
    def test_frozen(self) -> None:
        note = IssueNote(
            title="Test",
            slice=("core",),
        )

        with pytest.raises(pydantic.ValidationError):
            note.title = "changed"  # type: ignore[misc]

    def test_default_status(self) -> None:
        note = IssueNote(title="Test", slice=("core",))

        assert note.status == "planned"

    def test_default_story_count(self) -> None:
        note = IssueNote(title="Test", slice=("core",))

        assert note.story_count == 0

    def test_default_tags(self) -> None:
        note = IssueNote(title="Test", slice=("core",))

        assert note.tags == ("type/issue", "status/planned")

    def test_blocked_by_defaults_empty(self) -> None:
        note = IssueNote(title="Test", slice=("core",))

        assert note.blocked_by == ()

    def test_verification_defaults_none(self) -> None:
        note = IssueNote(title="Test", slice=("core",))

        assert note.verification is None

    def test_skills_required_default(self) -> None:
        note = IssueNote(title="t", slice=("core",))

        assert note.skills_required == ()


# ── save_issue ──────────────────────────────────────────────────


class TestSaveIssue:
    @patch(
        "mantle.core.issues.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_first_issue_at_expected_path(
        self, _mock: object, project: Path
    ) -> None:
        _, path = _save(project)

        expected = (
            project
            / ".mantle"
            / "issues"
            / "issue-01-context-compilation-engine.md"
        )
        assert path == expected
        assert path.exists()

    @patch(
        "mantle.core.issues.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_auto_assigns_second_number(
        self, _mock: object, project: Path
    ) -> None:
        _save(project)
        _, path = _save(project, title="Second issue")

        assert path.name == "issue-02-second-issue.md"

    @patch(
        "mantle.core.issues.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_correct_frontmatter(self, _mock: object, project: Path) -> None:
        note, _ = _save(
            project,
            title="Context engine",
            slice=("core", "cli"),
            blocked_by=(1, 2),
        )

        assert note.title == "Context engine"
        assert note.status == "planned"
        assert note.slice == ("core", "cli")
        assert note.story_count == 0
        assert note.blocked_by == (1, 2)
        assert note.tags == ("type/issue", "status/planned")

    @patch(
        "mantle.core.issues.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_round_trip_frontmatter(self, _mock: object, project: Path) -> None:
        saved_note, path = _save(project)
        loaded_note, _ = load_issue(path)

        assert loaded_note.title == saved_note.title
        assert loaded_note.status == saved_note.status
        assert loaded_note.slice == saved_note.slice
        assert loaded_note.story_count == saved_note.story_count
        assert loaded_note.blocked_by == saved_note.blocked_by
        assert loaded_note.tags == saved_note.tags

    @patch(
        "mantle.core.issues.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_round_trip_body(self, _mock: object, project: Path) -> None:
        _, path = _save(project)
        _, body = load_issue(path)

        assert CONTENT in body

    @patch(
        "mantle.core.issues.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_raises_on_exists(self, _mock: object, project: Path) -> None:
        _save(project, issue=1)

        with pytest.raises(IssueExistsError):
            _save(project, issue=1)

    @patch(
        "mantle.core.issues.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_overwrite_replaces(self, _mock: object, project: Path) -> None:
        _save(project, issue=1)
        note, path = _save(
            project,
            issue=1,
            title="Updated title",
            overwrite=True,
        )

        assert note.title == "Updated title"
        assert path.exists()

    @patch(
        "mantle.core.issues.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_transitions_from_system_design(
        self, _mock: object, project: Path
    ) -> None:
        _save(project)
        note = vault.read_note(project / ".mantle" / "state.md", ProjectState)

        assert note.frontmatter.status == Status.PLANNING

    @patch(
        "mantle.core.issues.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_transitions_from_adopted(
        self, _mock: object, project: Path
    ) -> None:
        _write_state(project, status=Status.ADOPTED)
        _save(project)
        note = vault.read_note(project / ".mantle" / "state.md", ProjectState)

        assert note.frontmatter.status == Status.PLANNING

    @patch(
        "mantle.core.issues.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_stays_in_planning(self, _mock: object, project: Path) -> None:
        _write_state(project, status=Status.PLANNING)
        _save(project)
        note = vault.read_note(project / ".mantle" / "state.md", ProjectState)

        assert note.frontmatter.status == Status.PLANNING

    @patch(
        "mantle.core.issues.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_updates_current_focus(self, _mock: object, project: Path) -> None:
        _save(project)
        text = (project / ".mantle" / "state.md").read_text()

        assert "Issue 1 planned" in text
        assert "/mantle:plan-issues" in text
        assert "/mantle:build" in text

    @patch(
        "mantle.core.issues.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_save_issue_with_skills_required(
        self, _mock: object, project: Path
    ) -> None:
        note, path = save_issue(
            project,
            CONTENT,
            title="Skill test",
            slice=("core",),
            skills_required=("cyclopts",),
        )

        assert note.skills_required == ("cyclopts",)
        loaded, _ = load_issue(path)
        assert loaded.skills_required == ("cyclopts",)


# ── load_issue ──────────────────────────────────────────────────


class TestLoadIssue:
    @patch(
        "mantle.core.issues.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_reads_saved(self, _mock: object, project: Path) -> None:
        _, path = _save(project)
        note, body = load_issue(path)

        assert note.title == "Context compilation engine"
        assert CONTENT in body

    def test_file_not_found(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            load_issue(tmp_path / "nonexistent.md")


# ── list_issues ─────────────────────────────────────────────────


class TestListIssues:
    def test_empty_when_none(self, project: Path) -> None:
        assert list_issues(project) == []

    @patch(
        "mantle.core.issues.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_returns_sorted_paths(self, _mock: object, project: Path) -> None:
        _save(project, title="Second")
        _save(project, title="Third")
        paths = list_issues(project)

        assert len(paths) == 2
        assert paths[0].name == "issue-01-second.md"
        assert paths[1].name == "issue-02-third.md"

    @patch(
        "mantle.core.issues.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_sorts_by_filename(self, _mock: object, project: Path) -> None:
        _save(project, issue=2, title="Second")
        _save(project, issue=1, title="First")
        paths = list_issues(project)

        assert paths[0] < paths[1]


# ── next_issue_number ───────────────────────────────────────────


class TestNextIssueNumber:
    def test_returns_1_when_empty(self, project: Path) -> None:
        assert next_issue_number(project) == 1

    @patch(
        "mantle.core.issues.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_returns_n_plus_1(self, _mock: object, project: Path) -> None:
        _save(project)
        assert next_issue_number(project) == 2

    @patch(
        "mantle.core.issues.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_handles_gaps(self, _mock: object, project: Path) -> None:
        _save(project, issue=1, title="First")
        _save(project, issue=3, title="Third")

        assert next_issue_number(project) == 4

    @patch(
        "mantle.core.issues.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_scans_archive_when_computing_max(
        self, _mock: object, project: Path
    ) -> None:
        _save(project, issue=40, title="Fortieth")
        _save(project, issue=41, title="Forty-first")
        _create_archived_issue(project, 43)

        assert next_issue_number(project) == 44

    def test_returns_max_plus_1_when_only_archive_has_issues(
        self, project: Path
    ) -> None:
        _create_archived_issue(project, 1, slug="first-archived")
        _create_archived_issue(project, 2, slug="second-archived")
        _create_archived_issue(project, 3, slug="third-archived")

        assert next_issue_number(project) == 4

    @patch(
        "mantle.core.issues.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_works_when_archive_dir_missing(
        self, _mock: object, project: Path
    ) -> None:
        _save(project, issue=1, title="First")
        _save(project, issue=2, title="Second")

        assert next_issue_number(project) == 3


# ── issue_exists ────────────────────────────────────────────────


class TestIssueExists:
    def test_false_when_no_issues(self, project: Path) -> None:
        assert issue_exists(project, 1) is False

    @patch(
        "mantle.core.issues.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_true_after_saving(self, _mock: object, project: Path) -> None:
        _save(project)

        assert issue_exists(project, 1) is True


# ── count_issues ────────────────────────────────────────────────


class TestCountIssues:
    def test_zero_when_empty(self, project: Path) -> None:
        assert count_issues(project) == 0

    @patch(
        "mantle.core.issues.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_correct_count(self, _mock: object, project: Path) -> None:
        _save(project, title="First")
        _save(project, title="Second")

        assert count_issues(project) == 2


# ── transition_to_approved ───────────────────────────────────────


def _write_issue_direct(
    project_dir: Path,
    issue_number: int,
    *,
    status: str = "planned",
) -> Path:
    """Write a minimal issue file without state.md interaction."""
    title = f"Issue {issue_number}"
    note = IssueNote(
        title=title,
        status=status,
        slice=("core",),
        tags=("type/issue", f"status/{status}"),
    )
    slug = title.lower().replace(" ", "-")
    path = (
        project_dir
        / ".mantle"
        / "issues"
        / f"issue-{issue_number:02d}-{slug}.md"
    )
    vault.write_note(path, note, "## Acceptance Criteria\n\n- Done\n")
    return path


class TestTransitionToApproved:
    def test_transition_to_approved_from_verified(self, project: Path) -> None:
        """Verified issue transitions to approved."""
        _write_issue_direct(project, 10, status="verified")

        path = issues_mod.transition_to_approved(project, 10)

        note, _ = load_issue(path)
        assert note.status == "approved"
        assert "status/approved" in note.tags

    def test_transition_to_approved_invalid_status(self, project: Path) -> None:
        """Non-verified issue raises InvalidTransitionError."""
        _write_issue_direct(project, 11, status="planned")

        with pytest.raises(InvalidTransitionError):
            issues_mod.transition_to_approved(project, 11)


# ── transition_to_implementing ───────────────────────────────────


class TestTransitionToImplementing:
    def test_transition_to_implementing_from_verified(
        self, project: Path
    ) -> None:
        """Verified issue transitions back to implementing."""
        _write_issue_direct(project, 12, status="verified")

        path = issues_mod.transition_to_implementing(project, 12)

        note, _ = load_issue(path)
        assert note.status == "implementing"
        assert "status/implementing" in note.tags

    def test_transition_to_implementing_invalid_status(
        self, project: Path
    ) -> None:
        """Non-planned/non-verified issue raises error."""
        _write_issue_direct(project, 13, status="approved")

        with pytest.raises(InvalidTransitionError):
            issues_mod.transition_to_implementing(project, 13)

    def test_transition_to_implementing_idempotent(self, project: Path) -> None:
        """Implementing issue transitions to implementing (no-op, no error)."""
        _write_issue_direct(project, 14, status="implementing")

        path = issues_mod.transition_to_implementing(project, 14)

        note, _ = load_issue(path)
        assert note.status == "implementing"
        assert "status/implementing" in note.tags

    def test_transition_to_implementing_from_implemented(
        self, project: Path
    ) -> None:
        """Implemented issue transitions back to implementing."""
        _write_issue_direct(project, 15, status="implemented")

        path = issues_mod.transition_to_implementing(project, 15)

        note, _ = load_issue(path)
        assert note.status == "implementing"
        assert "status/implementing" in note.tags


# ── transition_to_implemented ────────────────────────────────────


class TestTransitionToImplemented:
    def test_transition_to_implemented_from_implementing(
        self, project: Path
    ) -> None:
        """Implementing issue transitions to implemented, status and tags updated."""
        _write_issue_direct(project, 20, status="implementing")

        path = issues_mod.transition_to_implemented(project, 20)

        note, _ = load_issue(path)
        assert note.status == "implemented"
        assert "status/implemented" in note.tags

    def test_transition_to_implemented_invalid_status(
        self, project: Path
    ) -> None:
        """Planned issue raises InvalidTransitionError."""
        _write_issue_direct(project, 21, status="planned")

        with pytest.raises(InvalidTransitionError):
            issues_mod.transition_to_implemented(project, 21)
