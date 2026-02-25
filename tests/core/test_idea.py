"""Tests for mantle.core.idea."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING
from unittest.mock import patch

import pydantic
import pytest

if TYPE_CHECKING:
    from pathlib import Path

from mantle.core.idea import (
    IdeaExistsError,
    IdeaNote,
    create_idea,
    idea_exists,
    load_idea,
    update_idea,
)
from mantle.core.state import ProjectState, Status
from mantle.core.vault import read_note, write_note

MOCK_EMAIL = "test@example.com"


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """Create a minimal .mantle/ with state.md."""
    (tmp_path / ".mantle").mkdir()
    _write_state(tmp_path)
    return tmp_path


def _mock_git_identity() -> str:
    return MOCK_EMAIL


def _write_state(
    project_dir: Path,
    *,
    body: str | None = None,
) -> None:
    """Write a state.md for testing."""
    state = ProjectState(
        project="test-project",
        status=Status.IDEA,
        confidence="0/10",
        created=date(2025, 1, 1),
        created_by=MOCK_EMAIL,
        updated=date(2025, 1, 1),
        updated_by=MOCK_EMAIL,
    )
    if body is None:
        body = (
            "## Summary\n\n"
            "_Describe the project in one or two sentences._\n\n"
            "## Current Focus\n\n"
            "_What are you working on right now?_\n"
        )
    path = project_dir / ".mantle" / "state.md"
    write_note(path, state, body)


def _create_idea(project_dir: Path, **overrides: object) -> IdeaNote:
    """Create an idea with sensible defaults."""
    defaults = {
        "problem": "Feedback loops are too slow",
        "insight": "Persistent context eliminates ramp-up time",
        "target_user": "Solo developers using Claude Code",
        "success_criteria": ["Ship in 2 weeks", "5 users onboarded"],
    }
    defaults.update(overrides)
    return create_idea(project_dir, **defaults)


# ── create_idea ──────────────────────────────────────────────────


class TestCreateIdea:
    @patch(
        "mantle.core.idea.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_correct_frontmatter(self, _mock: object, project: Path) -> None:
        result = _create_idea(project)

        assert result.problem == "Feedback loops are too slow"
        assert result.insight == ("Persistent context eliminates ramp-up time")
        assert result.target_user == "Solo developers using Claude Code"
        assert result.success_criteria == (
            "Ship in 2 weeks",
            "5 users onboarded",
        )

    @patch(
        "mantle.core.idea.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_file_created(self, _mock: object, project: Path) -> None:
        _create_idea(project)

        assert (project / ".mantle" / "idea.md").exists()

    @patch(
        "mantle.core.idea.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_round_trip(self, _mock: object, project: Path) -> None:
        created = _create_idea(project)
        loaded = load_idea(project)

        assert loaded.problem == created.problem
        assert loaded.insight == created.insight
        assert loaded.target_user == created.target_user
        assert loaded.success_criteria == created.success_criteria

    @patch(
        "mantle.core.idea.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_body_has_populated_sections(
        self, _mock: object, project: Path
    ) -> None:
        _create_idea(project)
        path = project / ".mantle" / "idea.md"
        text = path.read_text()

        assert "## Problem" in text
        assert "Feedback loops are too slow" in text
        assert "## Insight" in text
        assert "Persistent context eliminates ramp-up time" in text
        assert "## Target User" in text
        assert "Solo developers using Claude Code" in text
        assert "## Success Criteria" in text
        assert "- Ship in 2 weeks" in text
        assert "- 5 users onboarded" in text
        assert "## Open Questions" in text

    @patch(
        "mantle.core.idea.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_raises_on_existing(self, _mock: object, project: Path) -> None:
        _create_idea(project)

        with pytest.raises(IdeaExistsError):
            _create_idea(project)

    @patch(
        "mantle.core.idea.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_overwrite_works(self, _mock: object, project: Path) -> None:
        _create_idea(project)
        result = _create_idea(
            project,
            problem="New problem",
            overwrite=True,
        )

        assert result.problem == "New problem"

    @patch(
        "mantle.core.idea.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_git_identity_stamp(self, _mock: object, project: Path) -> None:
        result = _create_idea(project)

        assert result.author == MOCK_EMAIL
        assert result.updated_by == MOCK_EMAIL

    @patch(
        "mantle.core.idea.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_default_tags(self, _mock: object, project: Path) -> None:
        result = _create_idea(project)

        assert result.tags == ("type/idea", "phase/idea")

    @patch(
        "mantle.core.idea.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_state_summary_updated(self, _mock: object, project: Path) -> None:
        _create_idea(project)
        path = project / ".mantle" / "state.md"
        text = path.read_text()

        assert "Feedback loops are too slow" in text
        assert "Persistent context eliminates ramp-up time" in text
        assert "_Describe the project in one or two sentences._" not in text

    @patch(
        "mantle.core.idea.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_state_current_focus_updated(
        self, _mock: object, project: Path
    ) -> None:
        _create_idea(project)
        path = project / ".mantle" / "state.md"
        text = path.read_text()

        assert "Idea captured" in text
        assert "_What are you working on right now?_" not in text

    @patch(
        "mantle.core.idea.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_state_stays_idea(self, _mock: object, project: Path) -> None:
        _create_idea(project)
        note = read_note(project / ".mantle" / "state.md", ProjectState)

        assert note.frontmatter.status == Status.IDEA

    @patch(
        "mantle.core.idea.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_state_timestamps_refreshed(
        self, _mock: object, project: Path
    ) -> None:
        _create_idea(project)
        note = read_note(project / ".mantle" / "state.md", ProjectState)

        assert note.frontmatter.updated == date.today()
        assert note.frontmatter.updated_by == MOCK_EMAIL


# ── load_idea ────────────────────────────────────────────────────


class TestLoadIdea:
    @patch(
        "mantle.core.idea.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_reads_saved(self, _mock: object, project: Path) -> None:
        _create_idea(project)
        loaded = load_idea(project)

        assert loaded.problem == "Feedback loops are too slow"

    def test_file_not_found(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            load_idea(tmp_path)


# ── update_idea ──────────────────────────────────────────────────


class TestUpdateIdea:
    @patch(
        "mantle.core.idea.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_updates_provided_fields(
        self, _mock: object, project: Path
    ) -> None:
        _create_idea(project)
        result = update_idea(project, problem="Updated problem")

        assert result.problem == "Updated problem"

    @patch(
        "mantle.core.idea.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_preserves_unchanged_fields(
        self, _mock: object, project: Path
    ) -> None:
        _create_idea(project)
        result = update_idea(project, problem="Updated problem")

        assert result.insight == ("Persistent context eliminates ramp-up time")
        assert result.target_user == "Solo developers using Claude Code"
        assert result.success_criteria == (
            "Ship in 2 weeks",
            "5 users onboarded",
        )

    @patch(
        "mantle.core.idea.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_refreshes_timestamps(self, _mock: object, project: Path) -> None:
        _create_idea(project)
        result = update_idea(project, problem="Updated problem")

        assert result.updated == date.today()
        assert result.updated_by == MOCK_EMAIL

    def test_raises_when_missing(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            update_idea(tmp_path, problem="Nope")


# ── idea_exists ──────────────────────────────────────────────────


class TestIdeaExists:
    def test_false_before(self, project: Path) -> None:
        assert idea_exists(project) is False

    @patch(
        "mantle.core.idea.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_true_after(self, _mock: object, project: Path) -> None:
        _create_idea(project)

        assert idea_exists(project) is True


# ── IdeaNote model ───────────────────────────────────────────────


class TestIdeaNote:
    def test_frozen(self) -> None:
        note = IdeaNote(
            problem="Test problem",
            insight="Test insight",
            target_user="Devs",
            success_criteria=("a",),
            author="a@b.com",
            created=date.today(),
            updated=date.today(),
            updated_by="a@b.com",
        )

        with pytest.raises(pydantic.ValidationError):
            note.problem = "Changed"  # type: ignore[misc]
