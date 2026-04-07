"""Tests for mantle.core.scout."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from mantle.core import vault
from mantle.core.scout import (
    ScoutReport,
    list_scouts,
    load_scout,
    save_scout,
)
from mantle.core.state import ProjectState, Status

MOCK_EMAIL = "test@example.com"
CONTENT = "## Scout Report\n\nAnalysis of target repository."


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
    repo_url: str = "https://github.com/tiangolo/fastapi",
    repo_name: str = "fastapi",
    dimensions: tuple[str, ...] = (
        "architecture",
        "patterns",
        "testing",
    ),
) -> tuple[ScoutReport, Path]:
    """Save a scout report with sensible defaults."""
    return save_scout(
        project_dir,
        content,
        repo_url=repo_url,
        repo_name=repo_name,
        dimensions=dimensions,
    )


# -- save_scout ------------------------------------------------------


class TestSaveScout:
    @patch(
        "mantle.core.scout.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_save_scout_creates_file(
        self, _mock: object, project: Path
    ) -> None:
        _, path = _save(project)

        assert path.exists()
        today = date.today().isoformat()
        assert path.name == f"{today}-fastapi.md"

    @patch(
        "mantle.core.scout.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_save_scout_frontmatter(self, _mock: object, project: Path) -> None:
        saved_note, path = _save(project)
        loaded_note, _ = load_scout(path)

        assert loaded_note.date == saved_note.date
        assert loaded_note.author == saved_note.author
        assert loaded_note.repo_url == saved_note.repo_url
        assert loaded_note.repo_name == saved_note.repo_name
        assert loaded_note.dimensions == saved_note.dimensions
        assert loaded_note.tags == saved_note.tags

    @patch(
        "mantle.core.scout.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_save_scout_auto_increments(
        self, _mock: object, project: Path
    ) -> None:
        _, path1 = _save(project)
        _, path2 = _save(project)

        assert path1 != path2
        today = date.today().isoformat()
        assert path1.name == f"{today}-fastapi.md"
        assert path2.name == f"{today}-fastapi-2.md"

    @patch(
        "mantle.core.scout.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_save_scout_updates_state(
        self, _mock: object, project: Path
    ) -> None:
        _save(project)
        path = project / ".mantle" / "state.md"
        text = path.read_text()

        assert "scout" in text.lower()
        assert "fastapi" in text.lower()

    @patch(
        "mantle.core.scout.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_save_scout_strips_analysis_blocks(
        self, _mock: object, project: Path
    ) -> None:
        raw = (
            "<analysis>thinking...</analysis>\n\n## Real Content\n\nKeep this."
        )
        _, path = _save(project, raw)
        _, body = load_scout(path)

        assert "<analysis>" not in body
        assert "Real Content" in body


# -- load_scout ------------------------------------------------------


class TestLoadScout:
    @patch(
        "mantle.core.scout.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_load_scout_roundtrip(self, _mock: object, project: Path) -> None:
        _, path = _save(project)
        note, body = load_scout(path)

        assert note.repo_name == "fastapi"
        assert note.repo_url == "https://github.com/tiangolo/fastapi"
        assert note.dimensions == (
            "architecture",
            "patterns",
            "testing",
        )
        assert CONTENT in body


# -- list_scouts -----------------------------------------------------


class TestListScouts:
    def test_list_scouts_empty(self, project: Path) -> None:
        assert list_scouts(project) == []

    @patch(
        "mantle.core.scout.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_list_scouts_sorted(self, _mock: object, project: Path) -> None:
        _save(project, repo_name="alpha-repo")
        _save(project, repo_name="beta-repo")
        paths = list_scouts(project)

        assert len(paths) == 2
        assert paths[0] < paths[1]


# -- slugify via save_scout filename ---------------------------------


class TestSlugify:
    """Test slugification through the public save_scout interface."""

    @patch(
        "mantle.core.scout.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_slugify_special_chars(self, _mock: object, project: Path) -> None:
        today = date.today().isoformat()

        _, path = _save(project, repo_name="Hello World!!!")
        assert path.name == f"{today}-hello-world.md"

        _, path2 = _save(project, repo_name="my-repo_v2.0")
        assert path2.name == f"{today}-my-repo-v2-0.md"

        _, path3 = _save(project, repo_name="A" * 60)
        slug = path3.name[len(today) + 1 : -3]  # strip date- and .md
        assert len(slug) <= 40
