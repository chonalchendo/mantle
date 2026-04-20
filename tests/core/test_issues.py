"""Tests for mantle.core.issues."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING
from unittest.mock import patch

import pydantic
import pytest

if TYPE_CHECKING:
    from pathlib import Path

from inline_snapshot import snapshot

from mantle.core import archive as archive_mod
from mantle.core import issues as issues_mod
from mantle.core import vault
from mantle.core.acceptance import (
    AcceptanceCriterion,
    CriterionNotFoundError,
)
from mantle.core.issues import (
    InvalidTransitionError,
    IssueExistsError,
    IssueNote,
    UnresolvedAcceptanceCriteriaError,
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


# ── hook dispatch ───────────────────────────────────────────────


def test_transition_to_implementing_dispatches_hook(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """transition_to_implementing fires issue-implement-start hook."""
    project_dir = tmp_path
    (project_dir / ".mantle").mkdir()
    (project_dir / ".mantle" / "issues").mkdir()
    _write_state(project_dir, status=Status.PLANNING)
    _write_issue_direct(project_dir, 7, status="verified")

    calls: list[tuple[str, dict[str, object]]] = []
    monkeypatch.setattr(
        "mantle.core.issues.hooks.dispatch",
        lambda event, **kw: calls.append((event, kw)),
    )

    issues_mod.transition_to_implementing(project_dir, 7)

    assert calls == [
        (
            "issue-implement-start",
            {
                "issue": 7,
                "status": "implementing",
                "title": "Issue 7",
                "project_dir": project_dir,
            },
        )
    ]


def test_transition_to_verified_dispatches_hook(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """transition_to_verified fires issue-verify-done hook."""
    project_dir = tmp_path
    (project_dir / ".mantle").mkdir()
    (project_dir / ".mantle" / "issues").mkdir()
    _write_state(project_dir, status=Status.PLANNING)
    _write_issue_direct(project_dir, 7, status="implementing")

    calls: list[tuple[str, dict[str, object]]] = []
    monkeypatch.setattr(
        "mantle.core.issues.hooks.dispatch",
        lambda event, **kw: calls.append((event, kw)),
    )

    issues_mod.transition_to_verified(project_dir, 7)

    assert calls == [
        (
            "issue-verify-done",
            {
                "issue": 7,
                "status": "verified",
                "title": "Issue 7",
                "project_dir": project_dir,
            },
        )
    ]


def test_transition_to_approved_dispatches_hook(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """transition_to_approved fires issue-review-approved hook."""
    project_dir = tmp_path
    (project_dir / ".mantle").mkdir()
    (project_dir / ".mantle" / "issues").mkdir()
    _write_state(project_dir, status=Status.PLANNING)
    _write_issue_direct(project_dir, 7, status="verified")

    calls: list[tuple[str, dict[str, object]]] = []
    monkeypatch.setattr(
        "mantle.core.issues.hooks.dispatch",
        lambda event, **kw: calls.append((event, kw)),
    )

    issues_mod.transition_to_approved(project_dir, 7)

    assert calls == [
        (
            "issue-review-approved",
            {
                "issue": 7,
                "status": "approved",
                "title": "Issue 7",
                "project_dir": project_dir,
            },
        )
    ]


def test_failed_transition_does_not_dispatch_hook(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Failed transition raises InvalidTransitionError and hook does not fire."""
    project_dir = tmp_path
    (project_dir / ".mantle").mkdir()
    (project_dir / ".mantle" / "issues").mkdir()
    _write_state(project_dir, status=Status.PLANNING)
    _write_issue_direct(project_dir, 7, status="planned")

    calls: list[tuple[str, dict[str, object]]] = []
    monkeypatch.setattr(
        "mantle.core.issues.hooks.dispatch",
        lambda event, **kw: calls.append((event, kw)),
    )

    with pytest.raises(InvalidTransitionError):
        issues_mod.transition_to_verified(project_dir, 7)

    assert calls == []


def test_transition_to_implemented_does_not_dispatch_hook(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """transition_to_implemented is not in the event list — no hook fires."""
    project_dir = tmp_path
    (project_dir / ".mantle").mkdir()
    (project_dir / ".mantle" / "issues").mkdir()
    _write_state(project_dir, status=Status.PLANNING)
    _write_issue_direct(project_dir, 7, status="implementing")

    calls: list[tuple[str, dict[str, object]]] = []
    monkeypatch.setattr(
        "mantle.core.issues.hooks.dispatch",
        lambda event, **kw: calls.append((event, kw)),
    )

    issues_mod.transition_to_implemented(project_dir, 7)

    assert calls == []


# ── find_issue_path_including_archive ────────────────────────────


class TestFindIssuePathIncludingArchive:
    def test_returns_live_path_when_issue_is_live(self, project: Path) -> None:
        live = _write_issue_direct(project, 30, status="planned")

        result = issues_mod.find_issue_path_including_archive(project, 30)

        assert result == live

    def test_returns_archived_path_when_issue_archived(
        self, project: Path
    ) -> None:
        _write_issue_direct(project, 31, status="verified")
        archive_mod.archive_issue(project, 31)

        result = issues_mod.find_issue_path_including_archive(project, 31)

        assert result is not None
        assert result.parent.name == "issues"
        assert result.parent.parent.name == "archive"
        assert result.name.startswith("issue-31-")

    def test_returns_none_when_issue_unknown(self, project: Path) -> None:
        assert issues_mod.find_issue_path_including_archive(project, 99) is None

    def test_prefers_live_over_archive_when_both_exist(
        self, project: Path
    ) -> None:
        # Write, archive, then write a new live issue with the same
        # number — the live copy must win so retrospective/save-learning
        # targets the current work, not a stale archive entry.
        _write_issue_direct(project, 32, status="verified")
        archive_mod.archive_issue(project, 32)
        live = _write_issue_direct(project, 32, status="planned")

        result = issues_mod.find_issue_path_including_archive(project, 32)

        assert result == live


# ── Acceptance criteria — save / flip / gate / migrate ──────────


def _extract_ac_section(body: str) -> str:
    """Return just the '## Acceptance criteria' block (for assertions)."""
    lines = body.splitlines()
    out: list[str] = []
    in_section = False
    for line in lines:
        if line.startswith("## Acceptance criteria"):
            in_section = True
            out.append(line)
            continue
        if in_section and line.startswith("## "):
            break
        if in_section:
            out.append(line)
    return "\n".join(out).rstrip() + "\n"


class TestSaveIssueAcceptanceCriteria:
    @patch(
        "mantle.core.issues.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_save_issue_regenerates_ac_section_in_body(
        self, _mock: object, project: Path
    ) -> None:
        stale_body = (
            "## What to build\n\nBuild the thing.\n\n"
            "## Acceptance criteria\n\n"
            "- [ ] Stale item\n"
        )
        note, path = save_issue(
            project,
            stale_body,
            title="AC regen",
            slice=("core",),
        )
        updated = note.model_copy(
            update={
                "acceptance_criteria": (
                    AcceptanceCriterion(
                        id="ac-01",
                        text="First criterion",
                        passes=True,
                    ),
                    AcceptanceCriterion(
                        id="ac-02",
                        text="Second criterion",
                        passes=False,
                    ),
                )
            }
        )
        vault.write_note(
            path,
            updated,
            issues_mod.acceptance.replace_ac_section(
                stale_body,
                issues_mod.acceptance.render_ac_section(
                    updated.acceptance_criteria
                ),
            ),
        )

        _, body = load_issue(path)
        ac_block = _extract_ac_section(body)

        assert ac_block == snapshot("""\
## Acceptance criteria

- [x] ac-01: First criterion
- [ ] ac-02: Second criterion
""")
        assert "Stale item" not in body

    @patch(
        "mantle.core.issues.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_save_issue_preserves_body_when_criteria_empty(
        self, _mock: object, project: Path
    ) -> None:
        body_in = (
            "## What to build\n\nBuild.\n\n"
            "## Acceptance criteria\n\n"
            "- [ ] Legacy checkbox\n"
        )

        _, path = save_issue(
            project,
            body_in,
            title="No AC",
            slice=("core",),
        )

        _, body_out = load_issue(path)
        assert "Legacy checkbox" in body_out


class TestFlipAcceptanceCriterion:
    @patch(
        "mantle.core.issues.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_flip_acceptance_criterion_updates_passes_and_body(
        self, _mock: object, project: Path
    ) -> None:
        body = (
            "## What to build\n\nBuild.\n\n"
            "## Acceptance criteria\n\n"
            "- [ ] ac-01: First\n"
        )
        _, path = save_issue(
            project,
            body,
            title="Flip test",
            slice=("core",),
        )
        # Seed structured ACs on the saved issue.
        note, body = load_issue(path)
        note = note.model_copy(
            update={
                "acceptance_criteria": (
                    AcceptanceCriterion(id="ac-01", text="First"),
                )
            }
        )
        vault.write_note(
            path,
            note,
            issues_mod.acceptance.replace_ac_section(
                body,
                issues_mod.acceptance.render_ac_section(
                    note.acceptance_criteria
                ),
            ),
        )

        updated = issues_mod.flip_acceptance_criterion(
            project, 1, "ac-01", passes=True
        )

        assert updated.acceptance_criteria[0].passes is True
        _, new_body = load_issue(path)
        assert "- [x] ac-01: First" in new_body

    @patch(
        "mantle.core.issues.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_flip_acceptance_criterion_raises_on_unknown_ac(
        self, _mock: object, project: Path
    ) -> None:
        _, path = save_issue(
            project,
            "## What to build\n\nBuild.\n",
            title="Flip missing",
            slice=("core",),
        )
        note, body = load_issue(path)
        note = note.model_copy(
            update={
                "acceptance_criteria": (
                    AcceptanceCriterion(id="ac-01", text="Only"),
                )
            }
        )
        vault.write_note(
            path,
            note,
            issues_mod.acceptance.replace_ac_section(
                body,
                issues_mod.acceptance.render_ac_section(
                    note.acceptance_criteria
                ),
            ),
        )

        with pytest.raises(CriterionNotFoundError):
            issues_mod.flip_acceptance_criterion(
                project, 1, "ac-99", passes=True
            )


def _write_issue_with_acs(
    project_dir: Path,
    issue_number: int,
    *,
    status: str,
    criteria: tuple[AcceptanceCriterion, ...],
) -> Path:
    """Write an issue file directly with structured ACs for test setup."""
    title = f"Issue {issue_number}"
    note = IssueNote(
        title=title,
        status=status,
        slice=("core",),
        tags=("type/issue", f"status/{status}"),
        acceptance_criteria=criteria,
    )
    slug = title.lower().replace(" ", "-")
    path = (
        project_dir
        / ".mantle"
        / "issues"
        / f"issue-{issue_number:02d}-{slug}.md"
    )
    body = issues_mod.acceptance.render_ac_section(criteria)
    vault.write_note(path, note, body)
    return path


class TestTransitionToApprovedAcceptanceGate:
    def test_blocks_when_ac_pending(self, project: Path) -> None:
        _write_issue_with_acs(
            project,
            40,
            status="verified",
            criteria=(AcceptanceCriterion(id="ac-01", text="pending"),),
        )

        with pytest.raises(UnresolvedAcceptanceCriteriaError) as excinfo:
            issues_mod.transition_to_approved(project, 40)

        assert excinfo.value.issue_number == 40
        assert excinfo.value.failing == ("ac-01",)

    def test_allows_when_all_pass(self, project: Path) -> None:
        _write_issue_with_acs(
            project,
            41,
            status="verified",
            criteria=(
                AcceptanceCriterion(id="ac-01", text="a", passes=True),
                AcceptanceCriterion(id="ac-02", text="b", passes=True),
            ),
        )

        path = issues_mod.transition_to_approved(project, 41)

        note, _ = load_issue(path)
        assert note.status == "approved"

    def test_allows_when_waived(self, project: Path) -> None:
        _write_issue_with_acs(
            project,
            42,
            status="verified",
            criteria=(
                AcceptanceCriterion(id="ac-01", text="a", passes=True),
                AcceptanceCriterion(
                    id="ac-02",
                    text="b",
                    passes=False,
                    waived=True,
                    waiver_reason="deferred",
                ),
            ),
        )

        path = issues_mod.transition_to_approved(project, 42)

        note, _ = load_issue(path)
        assert note.status == "approved"

    def test_still_works_with_empty_criteria(self, project: Path) -> None:
        _write_issue_direct(project, 43, status="verified")

        path = issues_mod.transition_to_approved(project, 43)

        note, _ = load_issue(path)
        assert note.status == "approved"


class TestMigrateAllAcs:
    @patch(
        "mantle.core.issues.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_converts_markdown_checkboxes(
        self, _mock: object, project: Path
    ) -> None:
        body = (
            "## What to build\n\nBuild.\n\n"
            "## Acceptance criteria\n\n"
            "- [ ] First\n"
            "- [x] Second\n"
        )
        _, path = save_issue(
            project,
            body,
            title="Migrate me",
            slice=("core",),
        )

        results = issues_mod.migrate_all_acs(project)

        assert results == [(1, 2)]
        note, body_out = load_issue(path)
        assert tuple(c.id for c in note.acceptance_criteria) == (
            "ac-01",
            "ac-02",
        )
        assert note.acceptance_criteria[0].passes is False
        assert note.acceptance_criteria[1].passes is True
        assert "- [ ] ac-01: First" in body_out
        assert "- [x] ac-02: Second" in body_out

    @patch(
        "mantle.core.issues.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_skips_already_migrated(self, _mock: object, project: Path) -> None:
        _write_issue_with_acs(
            project,
            1,
            status="planned",
            criteria=(
                AcceptanceCriterion(id="ac-01", text="already", passes=True),
            ),
        )

        results = issues_mod.migrate_all_acs(project)

        assert results == []

    @patch(
        "mantle.core.issues.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_covers_archive(self, _mock: object, project: Path) -> None:
        # Create and archive an issue carrying a legacy checkbox section.
        body = (
            "## What to build\n\nBuild.\n\n"
            "## Acceptance criteria\n\n"
            "- [ ] Archived item\n"
        )
        save_issue(
            project,
            body,
            title="Archived work",
            slice=("core",),
        )
        # Force it through to a state that archive_issue accepts.
        issues_mod.transition_to_implementing(project, 1)
        issues_mod.transition_to_verified(project, 1)
        issues_mod.transition_to_approved(project, 1)
        archive_mod.archive_issue(project, 1)

        results = issues_mod.migrate_all_acs(project)

        assert results == [(1, 1)]
