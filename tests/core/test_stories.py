"""Tests for mantle.core.stories."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

import pydantic
import pytest

from mantle.core import vault
from mantle.core.issues import IssueNote
from mantle.core.state import ProjectState, Status
from mantle.core.stories import (
    StoryExistsError,
    StoryNote,
    count_stories,
    list_stories,
    load_story,
    next_story_number,
    save_story,
    story_exists,
)

if TYPE_CHECKING:
    from pathlib import Path

MOCK_EMAIL = "test@example.com"
CONTENT = (
    "## User Story\n\n"
    "As a developer, I want a thing so that it works.\n\n"
    "## Approach\n\n"
    "Follow the existing pattern.\n\n"
    "## Implementation\n\n"
    "Build the thing.\n\n"
    "## Tests\n\n"
    "- **test_thing**: verifies the thing works\n"
)


@pytest.fixture(autouse=True)
def _mock_git(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock git identity for all tests in this module."""
    monkeypatch.setattr(
        "mantle.core.state.resolve_git_identity",
        lambda: MOCK_EMAIL,
    )


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """Create a minimal .mantle/ with state.md, issues, and stories dirs."""
    (tmp_path / ".mantle").mkdir()
    (tmp_path / ".mantle" / "issues").mkdir()
    (tmp_path / ".mantle" / "stories").mkdir()
    _write_state(tmp_path)
    _write_issue(tmp_path, issue=1)
    return tmp_path


def _write_state(
    project_dir: Path,
    *,
    status: Status = Status.PLANNING,
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
    body = (
        "## Summary\n\n"
        "Test project\n\n"
        "## Current Focus\n\n"
        "Planning stories.\n\n"
        "## Blockers\n\n"
        "_Anything preventing progress?_\n"
    )
    vault.write_note(project_dir / ".mantle" / "state.md", st, body)


def _write_issue(
    project_dir: Path,
    *,
    issue: int = 1,
    title: str = "Test issue",
) -> None:
    """Write an issue file for testing."""
    note = IssueNote(
        title=title,
        slice=("core", "tests"),
    )
    body = "## What to build\n\nBuild the thing.\n"
    path = project_dir / ".mantle" / "issues" / f"issue-{issue:02d}.md"
    vault.write_note(path, note, body)


def _save(
    project_dir: Path,
    *,
    issue: int = 1,
    title: str = "Core module — data model and CRUD",
    content: str = CONTENT,
    story: int | None = None,
    overwrite: bool = False,
) -> tuple[StoryNote, Path]:
    """Save a story with sensible defaults."""
    return save_story(
        project_dir,
        content,
        issue=issue,
        title=title,
        story=story,
        overwrite=overwrite,
    )


# ── StoryNote model ────────────────────────────────────────────


class TestStoryNote:
    def test_frozen(self) -> None:
        note = StoryNote(issue=1, title="Test")

        with pytest.raises(pydantic.ValidationError):
            note.title = "changed"  # type: ignore[misc]

    def test_default_status(self) -> None:
        note = StoryNote(issue=1, title="Test")

        assert note.status == "planned"

    def test_default_failure_log(self) -> None:
        note = StoryNote(issue=1, title="Test")

        assert note.failure_log is None

    def test_default_tags(self) -> None:
        note = StoryNote(issue=1, title="Test")

        assert note.tags == ("type/story", "status/planned")


# ── save_story ─────────────────────────────────────────────────


class TestSaveStory:
    def test_writes_file(self, project: Path) -> None:
        _, path = _save(project)

        assert path.exists()

    def test_filename_pattern(self, project: Path) -> None:
        _, path = _save(project)

        assert path.name == "issue-01-story-01.md"

    def test_auto_assigns_first_number(self, project: Path) -> None:
        _, path = _save(project)

        assert path.name == "issue-01-story-01.md"

    def test_auto_assigns_second_number(self, project: Path) -> None:
        _save(project)
        _, path = _save(project, title="Second story")

        assert path.name == "issue-01-story-02.md"

    def test_correct_frontmatter(self, project: Path) -> None:
        note, _ = _save(project, title="Core module")

        assert note.issue == 1
        assert note.title == "Core module"
        assert note.status == "planned"
        assert note.failure_log is None
        assert note.tags == ("type/story", "status/planned")

    def test_round_trip_frontmatter(self, project: Path) -> None:
        saved_note, path = _save(project)
        loaded_note, _ = load_story(path)

        assert loaded_note.issue == saved_note.issue
        assert loaded_note.title == saved_note.title
        assert loaded_note.status == saved_note.status
        assert loaded_note.failure_log == saved_note.failure_log
        assert loaded_note.tags == saved_note.tags

    def test_round_trip_body(self, project: Path) -> None:
        _, path = _save(project)
        _, body = load_story(path)

        assert CONTENT in body

    def test_raises_on_exists(self, project: Path) -> None:
        _save(project, story=1)

        with pytest.raises(StoryExistsError):
            _save(project, story=1)

    def test_overwrite_replaces(self, project: Path) -> None:
        _save(project, story=1)
        note, path = _save(
            project,
            story=1,
            title="Updated title",
            overwrite=True,
        )

        assert note.title == "Updated title"
        assert path.exists()

    def test_updates_issue_story_count(self, project: Path) -> None:
        _save(project)

        issue_path = project / ".mantle" / "issues" / "issue-01.md"
        loaded = vault.read_note(issue_path, IssueNote)
        assert loaded.frontmatter.story_count == 1

    def test_story_count_reflects_actual(self, project: Path) -> None:
        _save(project, title="First")
        _save(project, title="Second")
        _save(project, title="Third")

        issue_path = project / ".mantle" / "issues" / "issue-01.md"
        loaded = vault.read_note(issue_path, IssueNote)
        assert loaded.frontmatter.story_count == 3

    def test_updates_state_current_focus(self, project: Path) -> None:
        _save(project)
        text = (project / ".mantle" / "state.md").read_text()

        assert "Issue 1" in text
        assert "1 stories planned" in text
        assert "/mantle:plan-stories" in text
        assert "/mantle:implement" in text


# ── load_story ─────────────────────────────────────────────────


class TestLoadStory:
    def test_reads_saved(self, project: Path) -> None:
        _, path = _save(project)
        note, body = load_story(path)

        assert note.title == "Core module — data model and CRUD"
        assert CONTENT in body

    def test_file_not_found(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            load_story(tmp_path / "nonexistent.md")


# ── list_stories ───────────────────────────────────────────────


class TestListStories:
    def test_empty_when_none(self, project: Path) -> None:
        assert list_stories(project, issue=1) == []

    def test_returns_sorted_paths(self, project: Path) -> None:
        _save(project, title="First")
        _save(project, title="Second")
        paths = list_stories(project, issue=1)

        assert len(paths) == 2
        assert paths[0].name == "issue-01-story-01.md"
        assert paths[1].name == "issue-01-story-02.md"

    def test_excludes_other_issues(self, project: Path) -> None:
        _write_issue(project, issue=2, title="Other issue")
        _save(project, issue=1, title="Issue 1 story")
        _save(project, issue=2, title="Issue 2 story")

        paths = list_stories(project, issue=1)
        assert len(paths) == 1
        assert "issue-01" in paths[0].name


# ── next_story_number ──────────────────────────────────────────


class TestNextStoryNumber:
    def test_returns_1_when_empty(self, project: Path) -> None:
        assert next_story_number(project, issue=1) == 1

    def test_returns_n_plus_1(self, project: Path) -> None:
        _save(project)

        assert next_story_number(project, issue=1) == 2

    def test_handles_gaps(self, project: Path) -> None:
        _save(project, story=1, title="First")
        _save(project, story=3, title="Third")

        assert next_story_number(project, issue=1) == 4


# ── story_exists ───────────────────────────────────────────────


class TestStoryExists:
    def test_false_when_no_stories(self, project: Path) -> None:
        assert story_exists(project, issue=1, story=1) is False

    def test_true_after_saving(self, project: Path) -> None:
        _save(project)

        assert story_exists(project, issue=1, story=1) is True


# ── count_stories ──────────────────────────────────────────────


class TestCountStories:
    def test_zero_when_empty(self, project: Path) -> None:
        assert count_stories(project, issue=1) == 0

    def test_correct_count(self, project: Path) -> None:
        _save(project, title="First")
        _save(project, title="Second")

        assert count_stories(project, issue=1) == 2
