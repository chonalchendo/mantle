"""Tests for mantle.core.decisions."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING
from unittest.mock import patch

import pydantic
import pytest

if TYPE_CHECKING:
    from pathlib import Path

from mantle.core.decisions import (
    DecisionNote,
    decision_exists,
    list_decisions,
    load_decision,
    save_decision,
)

MOCK_EMAIL = "test@example.com"


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """Create a minimal .mantle/ with decisions dir."""
    (tmp_path / ".mantle").mkdir()
    (tmp_path / ".mantle" / "decisions").mkdir()
    return tmp_path


def _mock_git_identity() -> str:
    return MOCK_EMAIL


def _save(
    project_dir: Path,
    *,
    topic: str = "framework-selection",
    decision: str = "Use FastAPI for the REST layer",
    alternatives: list[str] | None = None,
    rationale: str = "Best async support and OpenAPI generation",
    reversal_trigger: str = "Performance benchmarks show 2x slower",
    confidence: str = "8/10",
    reversible: str = "medium",
    scope: str = "system-design",
) -> tuple[DecisionNote, Path]:
    """Save a decision with sensible defaults."""
    if alternatives is None:
        alternatives = ["Flask", "Django REST"]
    return save_decision(
        project_dir,
        topic=topic,
        decision=decision,
        alternatives=alternatives,
        rationale=rationale,
        reversal_trigger=reversal_trigger,
        confidence=confidence,
        reversible=reversible,
        scope=scope,
    )


# ── save_decision ──────────────────────────────────────────────


class TestSaveDecision:
    @patch(
        "mantle.core.decisions.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_correct_frontmatter(self, _mock: object, project: Path) -> None:
        note, _ = _save(project)

        assert note.date == date.today()
        assert note.author == MOCK_EMAIL
        assert note.topic == "framework-selection"
        assert note.scope == "system-design"
        assert note.confidence == "8/10"
        assert note.reversible == "medium"

    @patch(
        "mantle.core.decisions.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_file_at_expected_path(self, _mock: object, project: Path) -> None:
        _, path = _save(project)

        today = date.today().isoformat()
        expected = (
            project
            / ".mantle"
            / "decisions"
            / f"{today}-framework-selection.md"
        )
        assert path == expected
        assert path.exists()

    @patch(
        "mantle.core.decisions.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_round_trip(self, _mock: object, project: Path) -> None:
        saved_note, path = _save(project)
        loaded_note, _ = load_decision(path)

        assert loaded_note.date == saved_note.date
        assert loaded_note.author == saved_note.author
        assert loaded_note.topic == saved_note.topic
        assert loaded_note.scope == saved_note.scope
        assert loaded_note.confidence == saved_note.confidence
        assert loaded_note.reversible == saved_note.reversible
        assert loaded_note.tags == saved_note.tags

    @patch(
        "mantle.core.decisions.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_body_sections_present(self, _mock: object, project: Path) -> None:
        _, path = _save(project)
        _, body = load_decision(path)

        assert "## Decision" in body
        assert "Use FastAPI" in body
        assert "## Alternatives Considered" in body
        assert "- Flask" in body
        assert "- Django REST" in body
        assert "## Rationale" in body
        assert "Best async support" in body
        assert "## Reversal Trigger" in body
        assert "Performance benchmarks" in body

    @patch(
        "mantle.core.decisions.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_auto_increment_on_collision(
        self, _mock: object, project: Path
    ) -> None:
        _, path1 = _save(project)
        _, path2 = _save(project)

        assert path1 != path2
        today = date.today().isoformat()
        assert path1.name == f"{today}-framework-selection.md"
        assert path2.name == f"{today}-framework-selection-2.md"

    @patch(
        "mantle.core.decisions.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_git_identity_stamped(self, _mock: object, project: Path) -> None:
        note, _ = _save(project)

        assert note.author == MOCK_EMAIL

    @patch(
        "mantle.core.decisions.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_default_tags(self, _mock: object, project: Path) -> None:
        note, _ = _save(project)

        assert note.tags == (
            "type/decision",
            "phase/system-design",
        )

    @patch(
        "mantle.core.decisions.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_decisions_dir_auto_created(
        self, _mock: object, tmp_path: Path
    ) -> None:
        (tmp_path / ".mantle").mkdir()
        # No decisions dir yet
        _, path = _save(tmp_path)

        assert path.exists()
        assert (tmp_path / ".mantle" / "decisions").is_dir()

    @patch(
        "mantle.core.decisions.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_topic_slugified(self, _mock: object, project: Path) -> None:
        note, path = _save(project, topic="My Cool Decision")

        assert note.topic == "my-cool-decision"
        today = date.today().isoformat()
        assert path.name == f"{today}-my-cool-decision.md"


# ── load_decision ──────────────────────────────────────────────


class TestLoadDecision:
    @patch(
        "mantle.core.decisions.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_reads_saved(self, _mock: object, project: Path) -> None:
        _, path = _save(project)
        note, body = load_decision(path)

        assert note.topic == "framework-selection"
        assert "Use FastAPI" in body

    def test_file_not_found(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            load_decision(tmp_path / "nonexistent.md")


# ── list_decisions ─────────────────────────────────────────────


class TestListDecisions:
    def test_empty_when_none(self, project: Path) -> None:
        assert list_decisions(project) == []

    @patch(
        "mantle.core.decisions.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_sorted_paths(self, _mock: object, project: Path) -> None:
        _save(project, topic="alpha")
        _save(project, topic="beta")
        paths = list_decisions(project)

        assert len(paths) == 2
        assert paths[0] < paths[1]


# ── decision_exists ────────────────────────────────────────────


class TestDecisionExists:
    def test_false_before(self, project: Path) -> None:
        assert decision_exists(project) is False

    @patch(
        "mantle.core.decisions.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_true_after(self, _mock: object, project: Path) -> None:
        _save(project)

        assert decision_exists(project) is True


# ── DecisionNote model ────────────────────────────────────────


class TestDecisionNote:
    def test_frozen(self) -> None:
        note = DecisionNote(
            date=date.today(),
            author="a@b.com",
            topic="test",
            scope="system-design",
            confidence="5/10",
            reversible="high",
        )

        with pytest.raises(pydantic.ValidationError):
            note.author = "changed@b.com"  # type: ignore[misc]
