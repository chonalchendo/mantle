"""Tests for mantle.core.challenge."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING
from unittest.mock import patch

import pydantic
import pytest

if TYPE_CHECKING:
    from pathlib import Path

from mantle.core import idea, vault
from mantle.core.challenge import (
    ChallengeNote,
    IdeaNotFoundError,
    challenge_exists,
    list_challenges,
    load_challenge,
    save_challenge,
)
from mantle.core.state import ProjectState, Status

MOCK_EMAIL = "test@example.com"
TRANSCRIPT = "## Challenge Transcript\n\nQ: Why this approach?\nA: Because..."


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """Create a minimal .mantle/ with state.md and idea.md."""
    (tmp_path / ".mantle").mkdir()
    (tmp_path / ".mantle" / "challenges").mkdir()
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
    project_dir: Path, transcript: str = TRANSCRIPT
) -> tuple[ChallengeNote, Path]:
    """Save a challenge with sensible defaults."""
    return save_challenge(project_dir, transcript)


# ── save_challenge ──────────────────────────────────────────────


class TestSaveChallenge:
    @patch(
        "mantle.core.challenge.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_correct_frontmatter(self, _mock: object, project: Path) -> None:
        note, _ = _save(project)

        assert note.date == date.today()
        assert note.author == MOCK_EMAIL
        assert note.problem_ref == "Feedback loops are too slow"
        assert note.insight_ref == (
            "Persistent context eliminates ramp-up time"
        )

    @patch(
        "mantle.core.challenge.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_file_at_expected_path(self, _mock: object, project: Path) -> None:
        _, path = _save(project)

        today = date.today().isoformat()
        expected = project / ".mantle" / "challenges" / f"{today}-challenge.md"
        assert path == expected
        assert path.exists()

    @patch(
        "mantle.core.challenge.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_round_trip(self, _mock: object, project: Path) -> None:
        saved_note, path = _save(project)
        loaded_note, _ = load_challenge(path)

        assert loaded_note.date == saved_note.date
        assert loaded_note.author == saved_note.author
        assert loaded_note.problem_ref == saved_note.problem_ref
        assert loaded_note.insight_ref == saved_note.insight_ref
        assert loaded_note.tags == saved_note.tags

    @patch(
        "mantle.core.challenge.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_transcript_in_body(self, _mock: object, project: Path) -> None:
        _, path = _save(project)
        _, body = load_challenge(path)

        assert TRANSCRIPT in body

    @patch(
        "mantle.core.challenge.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_raises_idea_not_found(self, _mock: object, tmp_path: Path) -> None:
        (tmp_path / ".mantle").mkdir()
        (tmp_path / ".mantle" / "challenges").mkdir()
        _write_state(tmp_path)

        with pytest.raises(IdeaNotFoundError):
            _save(tmp_path)

    @patch(
        "mantle.core.challenge.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_stamps_author(self, _mock: object, project: Path) -> None:
        note, _ = _save(project)

        assert note.author == MOCK_EMAIL

    @patch(
        "mantle.core.challenge.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_default_tags(self, _mock: object, project: Path) -> None:
        note, _ = _save(project)

        assert note.tags == ("type/challenge", "phase/challenge")

    @patch(
        "mantle.core.challenge.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_state_current_focus_updated(
        self, _mock: object, project: Path
    ) -> None:
        _save(project)
        path = project / ".mantle" / "state.md"
        text = path.read_text()

        assert "Challenge completed" in text

    @patch(
        "mantle.core.challenge.state.resolve_git_identity",
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
        "mantle.core.challenge.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_state_status_unchanged(self, _mock: object, project: Path) -> None:
        _save(project)
        note = vault.read_note(project / ".mantle" / "state.md", ProjectState)

        assert note.frontmatter.status == Status.IDEA

    @patch(
        "mantle.core.challenge.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_auto_increments_on_collision(
        self, _mock: object, project: Path
    ) -> None:
        _, path1 = _save(project)
        _, path2 = _save(project)

        assert path1 != path2
        today = date.today().isoformat()
        assert path1.name == f"{today}-challenge.md"
        assert path2.name == f"{today}-challenge-2.md"


# ── load_challenge ──────────────────────────────────────────────


class TestLoadChallenge:
    @patch(
        "mantle.core.challenge.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_reads_saved(self, _mock: object, project: Path) -> None:
        _, path = _save(project)
        note, body = load_challenge(path)

        assert note.problem_ref == "Feedback loops are too slow"
        assert note.insight_ref == (
            "Persistent context eliminates ramp-up time"
        )
        assert TRANSCRIPT in body

    def test_file_not_found(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            load_challenge(tmp_path / "nonexistent.md")


# ── list_challenges ─────────────────────────────────────────────


class TestListChallenges:
    def test_empty_when_none(self, project: Path) -> None:
        assert list_challenges(project) == []

    @patch(
        "mantle.core.challenge.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_sorted_paths(self, _mock: object, project: Path) -> None:
        _save(project)
        _save(project)
        paths = list_challenges(project)

        assert len(paths) == 2
        assert paths[0] < paths[1]


# ── challenge_exists ────────────────────────────────────────────


class TestChallengeExists:
    def test_false_before(self, project: Path) -> None:
        assert challenge_exists(project) is False

    @patch(
        "mantle.core.challenge.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_true_after(self, _mock: object, project: Path) -> None:
        _save(project)

        assert challenge_exists(project) is True


# ── ChallengeNote model ────────────────────────────────────────


class TestChallengeNote:
    def test_frozen(self) -> None:
        note = ChallengeNote(
            date=date.today(),
            author="a@b.com",
            problem_ref="Test problem",
            insight_ref="Test insight",
        )

        with pytest.raises(pydantic.ValidationError):
            note.author = "changed@b.com"  # type: ignore[misc]
