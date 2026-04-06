"""Tests for mantle.core.knowledge."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from mantle.core.knowledge import (
    DistillationNote,
    _slugify,
    find_distillation_by_topic,
    list_distillations,
    load_distillation,
    save_distillation,
)
from mantle.core.project import SUBDIRS

MOCK_EMAIL = "test@example.com"
CONTENT = "## Distillation\n\nSynthesized knowledge about testing."


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """Create a minimal .mantle/ with distillations/."""
    (tmp_path / ".mantle").mkdir()
    (tmp_path / ".mantle" / "distillations").mkdir()
    return tmp_path


def _mock_git_identity() -> str:
    return MOCK_EMAIL


def _save(
    project_dir: Path,
    content: str = CONTENT,
    *,
    topic: str = "Testing Best Practices",
    source_paths: tuple[str, ...] = (
        "sessions/2026-01-01-session.md",
        "learnings/pytest-tips.md",
    ),
) -> tuple[DistillationNote, Path]:
    """Save a distillation with sensible defaults."""
    return save_distillation(
        project_dir,
        content,
        topic=topic,
        source_paths=source_paths,
    )


# -- save_distillation -----------------------------------------------


class TestSaveDistillation:
    @patch(
        "mantle.core.knowledge.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_save_distillation_creates_file(
        self, _mock: object, project: Path
    ) -> None:
        _, path = _save(project)

        assert path.exists()

    @patch(
        "mantle.core.knowledge.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_save_distillation_source_count(
        self, _mock: object, project: Path
    ) -> None:
        note, _ = _save(project)

        assert note.source_count == 2

    @patch(
        "mantle.core.knowledge.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_save_distillation_source_paths_stored(
        self, _mock: object, project: Path
    ) -> None:
        _, path = _save(project)
        loaded_note, _ = load_distillation(path)

        assert loaded_note.source_paths == (
            "sessions/2026-01-01-session.md",
            "learnings/pytest-tips.md",
        )

    @patch(
        "mantle.core.knowledge.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_save_distillation_auto_increment(
        self, _mock: object, project: Path
    ) -> None:
        _, path1 = _save(project)
        _, path2 = _save(project)

        assert path1 != path2
        today = date.today().isoformat()
        assert path1.name == f"{today}-testing-best-practices.md"
        assert path2.name == f"{today}-testing-best-practices-2.md"


# -- load_distillation -----------------------------------------------


class TestLoadDistillation:
    @patch(
        "mantle.core.knowledge.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_load_distillation(
        self, _mock: object, project: Path
    ) -> None:
        _, path = _save(project)
        note, body = load_distillation(path)

        assert note.topic == "Testing Best Practices"
        assert note.author == MOCK_EMAIL
        assert note.source_count == 2
        assert CONTENT in body


# -- list_distillations ----------------------------------------------


class TestListDistillations:
    def test_list_distillations_empty(self, project: Path) -> None:
        assert list_distillations(project) == []

    @patch(
        "mantle.core.knowledge.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_list_distillations_sorted(
        self, _mock: object, project: Path
    ) -> None:
        _save(project, topic="First Topic")
        _save(project, topic="Second Topic")
        paths = list_distillations(project)

        assert len(paths) == 2
        assert paths[0] < paths[1]

    @patch(
        "mantle.core.knowledge.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_list_distillations_topic_filter(
        self, _mock: object, project: Path
    ) -> None:
        _save(project, topic="Testing Best Practices")
        _save(project, topic="Deployment Guide")
        paths = list_distillations(project, topic="testing")

        assert len(paths) == 1


# -- find_distillation_by_topic --------------------------------------


class TestFindDistillationByTopic:
    @patch(
        "mantle.core.knowledge.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_find_distillation_by_topic_found(
        self, _mock: object, project: Path
    ) -> None:
        _save(project, topic="Testing Best Practices")
        result = find_distillation_by_topic(
            project, "Testing Best Practices"
        )

        assert result is not None
        assert result.exists()

    def test_find_distillation_by_topic_not_found(
        self, project: Path
    ) -> None:
        result = find_distillation_by_topic(project, "Nonexistent")

        assert result is None


# -- _slugify --------------------------------------------------------


class TestSlugify:
    def test_slugify(self) -> None:
        assert _slugify("Testing Best Practices") == (
            "testing-best-practices"
        )
        assert _slugify("A" * 60) == "a" * 40
        assert _slugify("Hello World!!!") == "hello-world"


# -- SUBDIRS ---------------------------------------------------------


class TestSubdirs:
    def test_distillations_subdir_in_subdirs(self) -> None:
        assert "distillations" in SUBDIRS
