"""Tests for mantle.core.research."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING
from unittest.mock import patch

import pydantic
import pytest

if TYPE_CHECKING:
    from pathlib import Path

from mantle.core import idea, vault
from mantle.core.research import (
    IdeaNotFoundError,
    ResearchNote,
    list_research,
    load_research,
    research_exists,
    save_research,
)
from mantle.core.state import ProjectState, Status

MOCK_EMAIL = "test@example.com"
CONTENT = "## Summary\n\nKey findings from research."


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """Create a minimal .mantle/ with state.md and idea.md."""
    (tmp_path / ".mantle").mkdir()
    (tmp_path / ".mantle" / "research").mkdir()
    _write_state(tmp_path)
    _write_idea(tmp_path)
    return tmp_path


def _mock_git_identity() -> str:
    return MOCK_EMAIL


def _write_state(
    project_dir: Path,
    *,
    body: str | None = None,
) -> None:
    """Write a state.md for testing."""
    st = ProjectState(
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
            "Feedback loops are too slow"
            " — Persistent context eliminates ramp-up time\n\n"
            "## Current Focus\n\n"
            "Idea captured — run /mantle:challenge next.\n\n"
            "## Blockers\n\n"
            "_Anything preventing progress?_\n"
        )
    path = project_dir / ".mantle" / "state.md"
    vault.write_note(path, st, body)


def _write_idea(project_dir: Path) -> None:
    """Write an idea.md for testing."""
    note = idea.IdeaNote(
        problem="Feedback loops are too slow",
        insight="Persistent context eliminates ramp-up time",
        target_user="Solo developers using Claude Code",
        success_criteria=("Ship in 2 weeks", "5 users onboarded"),
        author=MOCK_EMAIL,
        created=date(2025, 1, 1),
        updated=date(2025, 1, 1),
        updated_by=MOCK_EMAIL,
    )
    body = (
        "## Problem\n\nFeedback loops are too slow\n\n"
        "## Insight\n\nPersistent context eliminates ramp-up time\n\n"
        "## Target User\n\nSolo developers using Claude Code\n\n"
        "## Success Criteria\n\n"
        "- Ship in 2 weeks\n- 5 users onboarded\n\n"
        "## Open Questions\n\n_What do you still need to learn?_\n"
    )
    path = project_dir / ".mantle" / "idea.md"
    vault.write_note(path, note, body)


def _save(
    project_dir: Path,
    content: str = CONTENT,
    *,
    focus: str = "feasibility",
    confidence: str = "7/10",
) -> tuple[ResearchNote, Path]:
    """Save research with sensible defaults."""
    return save_research(
        project_dir, content, focus=focus, confidence=confidence
    )


# ── save_research ────────────────────────────────────────────────


class TestSaveResearch:
    @patch(
        "mantle.core.research.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_correct_frontmatter(self, _mock: object, project: Path) -> None:
        note, _ = _save(project)

        assert note.date == date.today()
        assert note.author == MOCK_EMAIL
        assert note.focus == "feasibility"
        assert note.confidence == "7/10"
        assert note.idea_ref == "Feedback loops are too slow"

    @patch(
        "mantle.core.research.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_file_at_expected_path(self, _mock: object, project: Path) -> None:
        _, path = _save(project)

        today = date.today().isoformat()
        expected = project / ".mantle" / "research" / f"{today}-feasibility.md"
        assert path == expected
        assert path.exists()

    @patch(
        "mantle.core.research.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_round_trip(self, _mock: object, project: Path) -> None:
        saved_note, path = _save(project)
        loaded_note, _ = load_research(path)

        assert loaded_note.date == saved_note.date
        assert loaded_note.author == saved_note.author
        assert loaded_note.focus == saved_note.focus
        assert loaded_note.confidence == saved_note.confidence
        assert loaded_note.idea_ref == saved_note.idea_ref
        assert loaded_note.tags == saved_note.tags

    @patch(
        "mantle.core.research.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_content_in_body(self, _mock: object, project: Path) -> None:
        _, path = _save(project)
        _, body = load_research(path)

        assert CONTENT in body

    @patch(
        "mantle.core.research.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_raises_idea_not_found(self, _mock: object, tmp_path: Path) -> None:
        (tmp_path / ".mantle").mkdir()
        (tmp_path / ".mantle" / "research").mkdir()
        _write_state(tmp_path)

        with pytest.raises(IdeaNotFoundError):
            _save(tmp_path)

    @patch(
        "mantle.core.research.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_stamps_author(self, _mock: object, project: Path) -> None:
        note, _ = _save(project)

        assert note.author == MOCK_EMAIL

    @patch(
        "mantle.core.research.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_default_tags(self, _mock: object, project: Path) -> None:
        note, _ = _save(project)

        assert note.tags == ("type/research", "phase/research")

    @patch(
        "mantle.core.research.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_state_current_focus_updated(
        self, _mock: object, project: Path
    ) -> None:
        _save(project)
        path = project / ".mantle" / "state.md"
        text = path.read_text()

        assert "Research (feasibility) completed" in text

    @patch(
        "mantle.core.research.state.resolve_git_identity",
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
        "mantle.core.research.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_state_status_unchanged(self, _mock: object, project: Path) -> None:
        _save(project)
        note = vault.read_note(project / ".mantle" / "state.md", ProjectState)

        assert note.frontmatter.status == Status.IDEA

    @patch(
        "mantle.core.research.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_auto_increments_on_collision(
        self, _mock: object, project: Path
    ) -> None:
        _, path1 = _save(project)
        _, path2 = _save(project)

        assert path1 != path2
        today = date.today().isoformat()
        assert path1.name == f"{today}-feasibility.md"
        assert path2.name == f"{today}-feasibility-2.md"

    @patch(
        "mantle.core.research.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_different_focus_no_collision(
        self, _mock: object, project: Path
    ) -> None:
        _, path1 = _save(project, focus="feasibility")
        _, path2 = _save(project, focus="competitive")

        today = date.today().isoformat()
        assert path1.name == f"{today}-feasibility.md"
        assert path2.name == f"{today}-competitive.md"

    def test_invalid_focus_raises_value_error(self, project: Path) -> None:
        with pytest.raises(ValueError, match="Invalid focus"):
            _save(project, focus="nonsense")

    def test_invalid_confidence_raises_value_error(self, project: Path) -> None:
        with pytest.raises(ValueError, match="Invalid confidence"):
            _save(project, confidence="high")


# ── load_research ────────────────────────────────────────────────


class TestLoadResearch:
    @patch(
        "mantle.core.research.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_reads_saved(self, _mock: object, project: Path) -> None:
        _, path = _save(project)
        note, body = load_research(path)

        assert note.idea_ref == "Feedback loops are too slow"
        assert CONTENT in body

    def test_file_not_found(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            load_research(tmp_path / "nonexistent.md")


# ── list_research ────────────────────────────────────────────────


class TestListResearch:
    def test_empty_when_none(self, project: Path) -> None:
        assert list_research(project) == []

    @patch(
        "mantle.core.research.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_sorted_paths(self, _mock: object, project: Path) -> None:
        _save(project, focus="feasibility")
        _save(project, focus="competitive")
        paths = list_research(project)

        assert len(paths) == 2
        assert paths[0] < paths[1]


# ── research_exists ──────────────────────────────────────────────


class TestResearchExists:
    def test_false_before(self, project: Path) -> None:
        assert research_exists(project) is False

    @patch(
        "mantle.core.research.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_true_after(self, _mock: object, project: Path) -> None:
        _save(project)

        assert research_exists(project) is True


# ── ResearchNote model ───────────────────────────────────────────


class TestResearchNote:
    def test_frozen(self) -> None:
        note = ResearchNote(
            date=date.today(),
            author="a@b.com",
            focus="general",
            confidence="5/10",
            idea_ref="Test problem",
        )

        with pytest.raises(pydantic.ValidationError):
            note.author = "changed@b.com"  # type: ignore[misc]
