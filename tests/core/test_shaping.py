"""Tests for mantle.core.shaping."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING
from unittest.mock import patch

import pydantic
import pytest

if TYPE_CHECKING:
    from pathlib import Path

from mantle.core import vault
from mantle.core.shaping import (
    ShapedIssueExistsError,
    ShapedIssueNote,
    list_shaped_issues,
    load_shaped_issue,
    save_shaped_issue,
    shaped_issue_exists,
)
from mantle.core.state import ProjectState, Status

MOCK_EMAIL = "test@example.com"
CONTENT = (
    "## Approach A\n\nDo it this way.\n\n"
    "## Approach B\n\nDo it that way.\n\n"
    "## Rationale\n\nApproach A is simpler."
)


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """Create a minimal .mantle/ with state.md."""
    (tmp_path / ".mantle").mkdir()
    (tmp_path / ".mantle" / "shaped").mkdir()
    _write_state(tmp_path)
    return tmp_path


def _mock_git_identity() -> str:
    return MOCK_EMAIL


def _write_state(
    project_dir: Path,
    *,
    status: Status = Status.PLANNING,
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
            "Planning issues.\n\n"
            "## Blockers\n\n"
            "_Anything preventing progress?_\n"
        )
    path = project_dir / ".mantle" / "state.md"
    vault.write_note(path, st, body)


def _save(
    project_dir: Path,
    *,
    issue: int = 21,
    title: str = "Shaping phase",
    approaches: tuple[str, ...] = ("Approach A", "Approach B"),
    chosen_approach: str = "Approach A",
    appetite: str = "medium batch",
    content: str = CONTENT,
    open_questions: tuple[str, ...] = (),
    overwrite: bool = False,
) -> tuple[ShapedIssueNote, Path]:
    """Save a shaped issue with sensible defaults."""
    return save_shaped_issue(
        project_dir,
        content,
        issue=issue,
        title=title,
        approaches=approaches,
        chosen_approach=chosen_approach,
        appetite=appetite,
        open_questions=open_questions,
        overwrite=overwrite,
    )


# ── save_shaped_issue ────────────────────────────────────────────


class TestSaveShapedIssue:
    @patch(
        "mantle.core.shaping.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_correct_frontmatter(self, _mock: object, project: Path) -> None:
        note, _ = _save(project)

        assert note.issue == 21
        assert note.title == "Shaping phase"
        assert note.approaches == ("Approach A", "Approach B")
        assert note.chosen_approach == "Approach A"
        assert note.appetite == "medium batch"
        assert note.open_questions == ()

    @patch(
        "mantle.core.shaping.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_file_at_expected_path(self, _mock: object, project: Path) -> None:
        _, path = _save(project)

        expected = (
            project / ".mantle" / "shaped" / "issue-21-shaping-phase-shaped.md"
        )
        assert path == expected
        assert path.exists()

    @patch(
        "mantle.core.shaping.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_zero_padded_issue_number(
        self, _mock: object, project: Path
    ) -> None:
        _, path = _save(project, issue=3)

        assert path.name == "issue-03-shaping-phase-shaped.md"

    @patch(
        "mantle.core.shaping.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_round_trip(self, _mock: object, project: Path) -> None:
        saved_note, path = _save(project)
        loaded_note, _ = load_shaped_issue(path)

        assert loaded_note.issue == saved_note.issue
        assert loaded_note.title == saved_note.title
        assert loaded_note.approaches == saved_note.approaches
        assert loaded_note.chosen_approach == saved_note.chosen_approach
        assert loaded_note.appetite == saved_note.appetite
        assert loaded_note.tags == saved_note.tags

    @patch(
        "mantle.core.shaping.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_content_in_body(self, _mock: object, project: Path) -> None:
        _, path = _save(project)
        _, body = load_shaped_issue(path)

        assert CONTENT in body

    @patch(
        "mantle.core.shaping.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_raises_on_exists(self, _mock: object, project: Path) -> None:
        _save(project)

        with pytest.raises(ShapedIssueExistsError):
            _save(project)

    @patch(
        "mantle.core.shaping.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_overwrite_replaces(self, _mock: object, project: Path) -> None:
        _save(project)
        note, path = _save(
            project,
            chosen_approach="Approach B",
            overwrite=True,
        )

        assert note.chosen_approach == "Approach B"
        assert path.exists()

    @patch(
        "mantle.core.shaping.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_stamps_author(self, _mock: object, project: Path) -> None:
        note, _ = _save(project)

        assert note.author == MOCK_EMAIL

    @patch(
        "mantle.core.shaping.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_default_tags(self, _mock: object, project: Path) -> None:
        note, _ = _save(project)

        assert note.tags == ("type/shaped", "phase/shaping")

    @patch(
        "mantle.core.shaping.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_state_body_updated(self, _mock: object, project: Path) -> None:
        _save(project)
        text = (project / ".mantle" / "state.md").read_text()

        assert "Issue 21 shaped" in text
        assert "/mantle:plan-stories" in text

    @patch(
        "mantle.core.shaping.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_state_timestamps_refreshed(
        self, _mock: object, project: Path
    ) -> None:
        _save(project)
        note = vault.read_note(project / ".mantle" / "state.md", ProjectState)

        assert note.frontmatter.updated == date.today()
        assert note.frontmatter.updated_by == MOCK_EMAIL

    @patch(
        "mantle.core.shaping.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_status_unchanged(self, _mock: object, project: Path) -> None:
        _save(project)
        note = vault.read_note(project / ".mantle" / "state.md", ProjectState)

        assert note.frontmatter.status == Status.PLANNING


# ── load_shaped_issue ────────────────────────────────────────────


class TestLoadShapedIssue:
    @patch(
        "mantle.core.shaping.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_reads_saved(self, _mock: object, project: Path) -> None:
        _, path = _save(project)
        note, body = load_shaped_issue(path)

        assert note.issue == 21
        assert CONTENT in body

    def test_file_not_found(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            load_shaped_issue(tmp_path / "nonexistent.md")


# ── list_shaped_issues ───────────────────────────────────────────


class TestListShapedIssues:
    def test_empty_when_none(self, project: Path) -> None:
        assert list_shaped_issues(project) == []

    @patch(
        "mantle.core.shaping.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_sorted_paths(self, _mock: object, project: Path) -> None:
        _save(project, issue=2)
        _save(project, issue=1)
        paths = list_shaped_issues(project)

        assert len(paths) == 2
        assert paths[0] < paths[1]


# ── shaped_issue_exists ──────────────────────────────────────────


class TestShapedIssueExists:
    def test_false_before(self, project: Path) -> None:
        assert shaped_issue_exists(project, 21) is False

    @patch(
        "mantle.core.shaping.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_true_after(self, _mock: object, project: Path) -> None:
        _save(project)

        assert shaped_issue_exists(project, 21) is True

    @patch(
        "mantle.core.shaping.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_false_for_different_issue(
        self, _mock: object, project: Path
    ) -> None:
        _save(project)

        assert shaped_issue_exists(project, 99) is False


# ── ShapedIssueNote model ───────────────────────────────────────


class TestShapedIssueNote:
    def test_frozen(self) -> None:
        note = ShapedIssueNote(
            issue=1,
            title="Test",
            approaches=("A", "B"),
            chosen_approach="A",
            appetite="small batch",
            author="a@b.com",
            created=date.today(),
            updated=date.today(),
            updated_by="a@b.com",
        )

        with pytest.raises(pydantic.ValidationError):
            note.title = "changed"  # type: ignore[misc]
