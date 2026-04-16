"""Tests for mantle.core.learning."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING
from unittest.mock import patch

import pydantic
import pytest

if TYPE_CHECKING:
    from pathlib import Path

from mantle.core import archive, issues, learning, state, vault

MOCK_EMAIL = "test@example.com"
CONTENT = (
    "## What went well\n\nTests passed on first try.\n\n"
    "## Harder than expected\n\nAPI integration was tricky.\n\n"
    "## Wrong assumptions\n\nAssumed the SDK supported batch.\n\n"
    "## Recommendations\n\nAlways check SDK docs first."
)


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """Create a minimal .mantle/ with state.md and a few issues."""
    (tmp_path / ".mantle").mkdir()
    (tmp_path / ".mantle" / "learnings").mkdir()
    (tmp_path / ".mantle" / "issues").mkdir()
    _write_state(tmp_path)
    for issue_num in (1, 2, 3, 21):
        _write_issue(tmp_path, issue_num)
    return tmp_path


def _write_issue(project_dir: Path, issue: int) -> None:
    """Scaffold a minimal issue file under .mantle/issues/."""
    note = issues.IssueNote(
        title=f"Issue {issue}",
        status="implementing",
        slice=("core",),
        tags=("type/issue", "status/implementing"),
    )
    path = project_dir / ".mantle" / "issues" / f"issue-{issue:02d}-issue.md"
    vault.write_note(path, note, "## Acceptance Criteria\n\n- It works\n")


def _mock_git_identity() -> str:
    return MOCK_EMAIL


def _write_state(
    project_dir: Path,
    *,
    status: state.Status = state.Status.REVIEWING,
    body: str | None = None,
) -> None:
    """Write a state.md for testing."""
    st = state.ProjectState(
        project="test-project",
        status=status,
        confidence="7/10",
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
            "Reviewing issue 21.\n\n"
            "## Blockers\n\n"
            "_Anything preventing progress?_\n"
        )
    path = project_dir / ".mantle" / "state.md"
    vault.write_note(path, st, body)


def _save(
    project_dir: Path,
    *,
    issue: int = 21,
    title: str = "Shaping phase implementation",
    confidence_delta: str = "+2",
    content: str = CONTENT,
    overwrite: bool = False,
) -> tuple[learning.LearningNote, Path]:
    """Save a learning with sensible defaults."""
    return learning.save_learning(
        project_dir,
        content,
        issue=issue,
        title=title,
        confidence_delta=confidence_delta,
        overwrite=overwrite,
    )


# ── save_learning ────────────────────────────────────────────────


class TestSaveLearning:
    @patch(
        "mantle.core.learning.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_correct_frontmatter(self, _mock: object, project: Path) -> None:
        note, _ = _save(project)

        assert note.issue == 21
        assert note.title == "Shaping phase implementation"
        assert note.confidence_delta == "+2"
        assert note.date == date.today()

    @patch(
        "mantle.core.learning.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_file_at_expected_path(self, _mock: object, project: Path) -> None:
        _, path = _save(project)

        expected = (
            project
            / ".mantle"
            / "learnings"
            / "issue-21-shaping-phase-implementation.md"
        )
        assert path == expected
        assert path.exists()

    @patch(
        "mantle.core.learning.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_zero_padded_issue_number(
        self, _mock: object, project: Path
    ) -> None:
        _, path = _save(project, issue=3)

        assert path.name == "issue-03-shaping-phase-implementation.md"

    @patch(
        "mantle.core.learning.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_round_trip(self, _mock: object, project: Path) -> None:
        saved_note, path = _save(project)
        loaded_note, _ = learning.load_learning(path)

        assert loaded_note.issue == saved_note.issue
        assert loaded_note.title == saved_note.title
        assert loaded_note.confidence_delta == (saved_note.confidence_delta)
        assert loaded_note.tags == saved_note.tags

    @patch(
        "mantle.core.learning.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_content_in_body(self, _mock: object, project: Path) -> None:
        _, path = _save(project)
        _, body = learning.load_learning(path)

        assert CONTENT in body

    @patch(
        "mantle.core.learning.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_raises_on_exists(self, _mock: object, project: Path) -> None:
        _save(project)

        with pytest.raises(learning.LearningExistsError):
            _save(project)

    @patch(
        "mantle.core.learning.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_overwrite_replaces(self, _mock: object, project: Path) -> None:
        _save(project)
        note, path = _save(
            project,
            confidence_delta="+3",
            overwrite=True,
        )

        assert note.confidence_delta == "+3"
        assert path.exists()

    @patch(
        "mantle.core.learning.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_stamps_author(self, _mock: object, project: Path) -> None:
        note, _ = _save(project)

        assert note.author == MOCK_EMAIL

    @patch(
        "mantle.core.learning.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_default_tags(self, _mock: object, project: Path) -> None:
        note, _ = _save(project)

        assert note.tags == ("type/learning", "phase/reviewing")

    @patch(
        "mantle.core.learning.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_state_body_updated(self, _mock: object, project: Path) -> None:
        _save(project)
        text = (project / ".mantle" / "state.md").read_text()

        assert "Learning captured for issue 21" in text
        assert "review past learnings" in text

    @patch(
        "mantle.core.learning.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_state_timestamps_refreshed(
        self, _mock: object, project: Path
    ) -> None:
        _save(project)
        note = vault.read_note(
            project / ".mantle" / "state.md", state.ProjectState
        )

        assert note.frontmatter.updated == date.today()
        assert note.frontmatter.updated_by == MOCK_EMAIL

    @patch(
        "mantle.core.learning.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_status_unchanged(self, _mock: object, project: Path) -> None:
        _save(project)
        note = vault.read_note(
            project / ".mantle" / "state.md", state.ProjectState
        )

        assert note.frontmatter.status == state.Status.REVIEWING

    @patch(
        "mantle.core.learning.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_invalid_confidence_delta_raises(
        self, _mock: object, project: Path
    ) -> None:
        with pytest.raises(ValueError, match="Invalid confidence_delta"):
            _save(project, confidence_delta="2")

    @patch(
        "mantle.core.learning.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_invalid_confidence_delta_no_sign(
        self, _mock: object, project: Path
    ) -> None:
        with pytest.raises(ValueError):
            _save(project, confidence_delta="10")

    @patch(
        "mantle.core.learning.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_invalid_confidence_delta_three_digits(
        self, _mock: object, project: Path
    ) -> None:
        with pytest.raises(ValueError):
            _save(project, confidence_delta="+100")

    @patch(
        "mantle.core.learning.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_valid_positive_delta(self, _mock: object, project: Path) -> None:
        note, _ = _save(project, confidence_delta="+5")

        assert note.confidence_delta == "+5"

    @patch(
        "mantle.core.learning.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_valid_negative_delta(self, _mock: object, project: Path) -> None:
        note, _ = _save(project, confidence_delta="-3")

        assert note.confidence_delta == "-3"

    @patch(
        "mantle.core.learning.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_valid_two_digit_delta(self, _mock: object, project: Path) -> None:
        note, _ = _save(project, confidence_delta="+10")

        assert note.confidence_delta == "+10"

    def test_save_learning_raises_when_issue_missing(
        self, project: Path
    ) -> None:
        with pytest.raises(learning.IssueNotFoundError):
            _save(project, issue=99)

        learnings_dir = project / ".mantle" / "learnings"
        assert list(learnings_dir.glob("*.md")) == []

    @patch(
        "mantle.core.learning.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_save_learning_raises_when_issue_archived(
        self, _mock: object, project: Path
    ) -> None:
        # Scaffold issue 50 in .mantle/issues/ then archive it.
        (project / ".mantle" / "issues").mkdir(exist_ok=True)
        issue_note = issues.IssueNote(
            title="Test issue",
            status="verified",
            slice=("core",),
            tags=("type/issue", "status/verified"),
        )
        issue_path = project / ".mantle" / "issues" / "issue-50-test-issue.md"
        vault.write_note(
            issue_path,
            issue_note,
            "## Acceptance Criteria\n\n- It works\n",
        )

        archive.archive_issue(project, 50)

        with pytest.raises(learning.IssueNotFoundError):
            _save(project, issue=50)

        learnings_dir = project / ".mantle" / "learnings"
        assert list(learnings_dir.glob("*.md")) == []


# ── load_learning ────────────────────────────────────────────────


class TestLoadLearning:
    @patch(
        "mantle.core.learning.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_reads_saved(self, _mock: object, project: Path) -> None:
        _, path = _save(project)
        note, body = learning.load_learning(path)

        assert note.issue == 21
        assert CONTENT in body

    def test_file_not_found(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            learning.load_learning(tmp_path / "nonexistent.md")


# ── list_learnings ───────────────────────────────────────────────


class TestListLearnings:
    def test_empty_when_none(self, project: Path) -> None:
        assert learning.list_learnings(project) == []

    @patch(
        "mantle.core.learning.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_sorted_paths(self, _mock: object, project: Path) -> None:
        _save(project, issue=2)
        _save(project, issue=1)
        paths = learning.list_learnings(project)

        assert len(paths) == 2
        assert paths[0] < paths[1]


# ── learning_exists ──────────────────────────────────────────────


class TestLearningExists:
    def test_false_before(self, project: Path) -> None:
        assert learning.learning_exists(project, 21) is False

    @patch(
        "mantle.core.learning.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_true_after(self, _mock: object, project: Path) -> None:
        _save(project)

        assert learning.learning_exists(project, 21) is True

    @patch(
        "mantle.core.learning.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_false_for_different_issue(
        self, _mock: object, project: Path
    ) -> None:
        _save(project)

        assert learning.learning_exists(project, 99) is False


# ── LearningNote model ──────────────────────────────────────────


class TestLearningNote:
    def test_frozen(self) -> None:
        note = learning.LearningNote(
            issue=1,
            title="Test",
            author="a@b.com",
            date=date.today(),
            confidence_delta="+1",
        )

        with pytest.raises(pydantic.ValidationError):
            note.title = "changed"  # type: ignore[misc]
