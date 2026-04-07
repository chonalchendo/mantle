"""Tests for mantle.core.brainstorm."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from mantle.core import vault
from mantle.core.brainstorm import (
    BrainstormNote,
    brainstorm_exists,
    list_brainstorms,
    load_brainstorm,
    save_brainstorm,
)
from mantle.core.state import ProjectState, Status

MOCK_EMAIL = "test@example.com"
CONTENT = "## Brainstorm\n\nWhat if we added interactive queries?"


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """Create a minimal .mantle/ with state.md and brainstorms/."""
    (tmp_path / ".mantle").mkdir()
    (tmp_path / ".mantle" / "brainstorms").mkdir()
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
    st = ProjectState(
        project="test-project",
        status=Status.PLANNING,
        confidence="0/10",
        created=date(2025, 1, 1),
        created_by=MOCK_EMAIL,
        updated=date(2025, 1, 1),
        updated_by=MOCK_EMAIL,
    )
    if body is None:
        body = (
            "## Summary\n\n"
            "Test project summary\n\n"
            "## Current Focus\n\n"
            "Planning in progress.\n\n"
            "## Blockers\n\n"
            "_Anything preventing progress?_\n"
        )
    path = project_dir / ".mantle" / "state.md"
    vault.write_note(path, st, body)


def _save(
    project_dir: Path,
    content: str = CONTENT,
    *,
    title: str = "MotherdDuck Interactive Queries",
    verdict: str = "proceed",
) -> tuple[BrainstormNote, Path]:
    """Save a brainstorm with sensible defaults."""
    return save_brainstorm(project_dir, content, title=title, verdict=verdict)


# -- save_brainstorm ------------------------------------------------


class TestSaveBrainstorm:
    @patch(
        "mantle.core.brainstorm.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_save_brainstorm_creates_file(
        self, _mock: object, project: Path
    ) -> None:
        _, path = _save(project)

        assert path.exists()

    @patch(
        "mantle.core.brainstorm.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_save_brainstorm_frontmatter(
        self, _mock: object, project: Path
    ) -> None:
        saved_note, path = _save(project)
        loaded_note, _ = load_brainstorm(path)

        assert loaded_note.date == saved_note.date
        assert loaded_note.author == saved_note.author
        assert loaded_note.title == saved_note.title
        assert loaded_note.verdict == saved_note.verdict
        assert loaded_note.tags == saved_note.tags

    @patch(
        "mantle.core.brainstorm.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_save_brainstorm_strips_analysis(
        self, _mock: object, project: Path
    ) -> None:
        raw = (
            "<analysis>thinking...</analysis>\n\n## Real Content\n\nKeep this."
        )
        _, path = _save(project, raw)
        _, body = load_brainstorm(path)

        assert "<analysis>" not in body
        assert "Real Content" in body

    @patch(
        "mantle.core.brainstorm.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_save_brainstorm_auto_increments(
        self, _mock: object, project: Path
    ) -> None:
        _, path1 = _save(project)
        _, path2 = _save(project)

        assert path1 != path2
        today = date.today().isoformat()
        assert path1.name == f"{today}-motherdduck-interactive-queries.md"
        assert path2.name == (f"{today}-motherdduck-interactive-queries-2.md")

    def test_save_brainstorm_invalid_verdict(self, project: Path) -> None:
        with pytest.raises(ValueError, match="Invalid verdict"):
            _save(project, verdict="maybe")

    @patch(
        "mantle.core.brainstorm.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_save_brainstorm_updates_state(
        self, _mock: object, project: Path
    ) -> None:
        _save(project, verdict="proceed")
        path = project / ".mantle" / "state.md"
        text = path.read_text()

        assert "proceed" in text.lower()


# -- load_brainstorm ------------------------------------------------


class TestLoadBrainstorm:
    @patch(
        "mantle.core.brainstorm.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_load_brainstorm(self, _mock: object, project: Path) -> None:
        _, path = _save(project)
        note, body = load_brainstorm(path)

        assert note.title == "MotherdDuck Interactive Queries"
        assert note.verdict == "proceed"
        assert CONTENT in body


# -- list_brainstorms -----------------------------------------------


class TestListBrainstorms:
    def test_list_brainstorms_empty(self, project: Path) -> None:
        assert list_brainstorms(project) == []

    @patch(
        "mantle.core.brainstorm.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_list_brainstorms_sorted(
        self, _mock: object, project: Path
    ) -> None:
        _save(project, title="First Idea")
        _save(project, title="Second Idea")
        paths = list_brainstorms(project)

        assert len(paths) == 2
        assert paths[0] < paths[1]


# -- brainstorm_exists ----------------------------------------------


class TestBrainstormExists:
    def test_brainstorm_exists_false(self, project: Path) -> None:
        assert brainstorm_exists(project) is False

    @patch(
        "mantle.core.brainstorm.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_brainstorm_exists_true(self, _mock: object, project: Path) -> None:
        _save(project)

        assert brainstorm_exists(project) is True
