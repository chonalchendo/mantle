"""Tests for mantle.core.session."""

from __future__ import annotations

import warnings
from datetime import date, datetime
from typing import TYPE_CHECKING
from unittest.mock import patch

import pydantic
import pytest

if TYPE_CHECKING:
    from pathlib import Path

from mantle.core import vault
from mantle.core.session import (
    WORD_CAP,
    SessionNote,
    SessionTooLongWarning,
    count_words,
    latest_session,
    list_sessions,
    load_session,
    save_session,
    session_exists,
)
from mantle.core.state import ProjectState, Status

MOCK_EMAIL = "test@example.com"
OTHER_EMAIL = "other@example.com"
BODY = (
    "## Summary\n\n"
    "Implemented session logging.\n\n"
    "## What Was Done\n\n"
    "- Added core session module\n\n"
    "## Decisions Made\n\n"
    "- Warning, not error, for word cap\n\n"
    "## What's Next\n\n"
    "- Add CLI command\n\n"
    "## Open Questions\n\n"
    "None\n"
)


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """Create a minimal .mantle/ with state.md."""
    (tmp_path / ".mantle").mkdir()
    (tmp_path / ".mantle" / "sessions").mkdir()
    _write_state(tmp_path)
    return tmp_path


def _mock_git_identity() -> str:
    return MOCK_EMAIL


def _write_state(project_dir: Path) -> None:
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
    body = (
        "## Summary\n\n"
        "Test project\n\n"
        "## Current Focus\n\n"
        "Idea captured.\n\n"
        "## Blockers\n\n"
        "None\n"
    )
    path = project_dir / ".mantle" / "state.md"
    vault.write_note(path, st, body)


def _save(
    project_dir: Path,
    content: str = BODY,
    *,
    commands_used: tuple[str, ...] = (),
) -> tuple[SessionNote, Path]:
    """Save a session with sensible defaults."""
    return save_session(
        project_dir, content, commands_used=commands_used
    )


# ── save_session ─────────────────────────────────────────────────


class TestSaveSession:
    @patch(
        "mantle.core.session.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_writes_file(
        self, _mock: object, project: Path
    ) -> None:
        _, path = _save(project)

        assert path.exists()
        assert path.parent.name == "sessions"

    @patch(
        "mantle.core.session.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_filename_pattern(
        self, _mock: object, project: Path
    ) -> None:
        _, path = _save(project)

        # Format: YYYY-MM-DD-HHMM.md
        stem = path.stem
        parts = stem.split("-")
        assert len(parts) >= 4
        assert len(parts[0]) == 4  # year
        assert len(parts[1]) == 2  # month
        assert len(parts[2]) == 2  # day
        assert len(parts[3]) == 4  # HHMM

    @patch(
        "mantle.core.session.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_correct_frontmatter(
        self, _mock: object, project: Path
    ) -> None:
        note, _ = _save(
            project, commands_used=("idea", "challenge")
        )

        assert note.project == "test-project"
        assert note.author == MOCK_EMAIL
        assert note.commands_used == ("idea", "challenge")

    @patch(
        "mantle.core.session.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_round_trip_frontmatter(
        self, _mock: object, project: Path
    ) -> None:
        saved_note, path = _save(project)
        loaded_note, _ = load_session(path)

        assert loaded_note.project == saved_note.project
        assert loaded_note.author == saved_note.author
        assert loaded_note.commands_used == saved_note.commands_used
        assert loaded_note.tags == saved_note.tags

    @patch(
        "mantle.core.session.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_round_trip_body(
        self, _mock: object, project: Path
    ) -> None:
        _, path = _save(project)
        _, body = load_session(path)

        assert BODY in body

    @patch(
        "mantle.core.session.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_stamps_author(
        self, _mock: object, project: Path
    ) -> None:
        note, _ = _save(project)

        assert note.author == MOCK_EMAIL

    @patch(
        "mantle.core.session.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_project_from_state(
        self, _mock: object, project: Path
    ) -> None:
        note, _ = _save(project)

        assert note.project == "test-project"

    @patch(
        "mantle.core.session.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_date_is_datetime(
        self, _mock: object, project: Path
    ) -> None:
        note, _ = _save(project)

        assert isinstance(note.date, datetime)

    @patch(
        "mantle.core.session.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_commands_used_stored(
        self, _mock: object, project: Path
    ) -> None:
        note, _ = _save(
            project, commands_used=("idea", "challenge")
        )

        assert note.commands_used == ("idea", "challenge")

    @patch(
        "mantle.core.session.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_empty_commands_default(
        self, _mock: object, project: Path
    ) -> None:
        note, _ = _save(project)

        assert note.commands_used == ()

    @patch(
        "mantle.core.session.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_default_tags(
        self, _mock: object, project: Path
    ) -> None:
        note, _ = _save(project)

        assert note.tags == ("type/session-log",)

    @patch(
        "mantle.core.session.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_warns_when_over_word_cap(
        self, _mock: object, project: Path
    ) -> None:
        long_body = " ".join(["word"] * (WORD_CAP + 50))

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _save(project, long_body)

        assert len(w) == 1
        assert issubclass(w[0].category, SessionTooLongWarning)

    @patch(
        "mantle.core.session.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_no_warning_under_word_cap(
        self, _mock: object, project: Path
    ) -> None:
        short_body = "Short session."

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _save(project, short_body)

        session_warnings = [
            x
            for x in w
            if issubclass(x.category, SessionTooLongWarning)
        ]
        assert len(session_warnings) == 0

    @patch(
        "mantle.core.session.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_auto_increments_on_collision(
        self, _mock: object, project: Path
    ) -> None:
        _, path1 = _save(project)
        _, path2 = _save(project)

        assert path1 != path2
        assert "-2" in path2.stem


# ── load_session ─────────────────────────────────────────────────


class TestLoadSession:
    @patch(
        "mantle.core.session.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_reads_saved(
        self, _mock: object, project: Path
    ) -> None:
        _, path = _save(project)
        note, body = load_session(path)

        assert note.project == "test-project"
        assert BODY in body

    def test_file_not_found(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            load_session(tmp_path / "nonexistent.md")


# ── list_sessions ────────────────────────────────────────────────


class TestListSessions:
    def test_empty_when_none(self, project: Path) -> None:
        assert list_sessions(project) == []

    @patch(
        "mantle.core.session.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_sorted_paths(
        self, _mock: object, project: Path
    ) -> None:
        _save(project)
        _save(project)
        paths = list_sessions(project)

        assert len(paths) == 2
        assert paths[0] < paths[1]

    @patch(
        "mantle.core.session.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_filters_by_author(
        self, _mock: object, project: Path
    ) -> None:
        _save(project)
        paths = list_sessions(project, author=MOCK_EMAIL)

        assert len(paths) == 1

    @patch(
        "mantle.core.session.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_returns_all_when_no_author(
        self, _mock: object, project: Path
    ) -> None:
        _save(project)
        paths_filtered = list_sessions(
            project, author=MOCK_EMAIL
        )
        paths_all = list_sessions(project)

        assert paths_filtered == paths_all


# ── session_exists ───────────────────────────────────────────────


class TestSessionExists:
    def test_false_when_none(self, project: Path) -> None:
        assert session_exists(project) is False

    @patch(
        "mantle.core.session.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_true_after_save(
        self, _mock: object, project: Path
    ) -> None:
        _save(project)

        assert session_exists(project) is True


# ── count_words ──────────────────────────────────────────────────


class TestCountWords:
    def test_simple_text(self) -> None:
        assert count_words("hello world foo bar") == 4

    def test_empty_string(self) -> None:
        assert count_words("") == 0


# ── SessionNote model ────────────────────────────────────────────


class TestSessionNote:
    def test_frozen(self) -> None:
        note = SessionNote(
            project="test",
            author="a@b.com",
            date=datetime.now(),
        )

        with pytest.raises(pydantic.ValidationError):
            note.author = "changed@b.com"  # type: ignore[misc]


# ── latest_session ──────────────────────────────────────────────


def _write_session(
    project_dir: Path,
    filename: str,
    *,
    author: str = MOCK_EMAIL,
    body: str = BODY,
    commands_used: tuple[str, ...] = (),
) -> None:
    """Write a session file directly (bypasses save_session)."""
    note = SessionNote(
        project="test-project",
        author=author,
        date=datetime(2026, 3, 1, 14, 30),
        commands_used=commands_used,
    )
    path = project_dir / ".mantle" / "sessions" / filename
    vault.write_note(path, note, body)


class TestLatestSession:
    def test_none_when_no_sessions(self, project: Path) -> None:
        assert latest_session(project) is None

    def test_returns_most_recent(self, project: Path) -> None:
        _write_session(
            project,
            "2026-03-01-1000.md",
            body="First session.",
        )
        _write_session(
            project,
            "2026-03-01-1400.md",
            body="Second session.",
        )

        result = latest_session(project)

        assert result is not None
        _, body = result
        assert "Second session." in body

    @patch(
        "mantle.core.session.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_returns_tuple(
        self, _mock: object, project: Path
    ) -> None:
        _save(project)

        result = latest_session(project)

        assert result is not None
        note, body = result
        assert isinstance(note, SessionNote)
        assert note.project == "test-project"
        assert note.author == MOCK_EMAIL
        assert isinstance(body, str)
        assert len(body) > 0

    def test_filters_by_author(self, project: Path) -> None:
        _write_session(
            project, "2026-03-01-1400.md", author=MOCK_EMAIL
        )
        _write_session(
            project,
            "2026-03-01-1500.md",
            author=OTHER_EMAIL,
            body="Other author session.",
        )

        result = latest_session(project, author=MOCK_EMAIL)

        assert result is not None
        note, _ = result
        assert note.author == MOCK_EMAIL

    def test_none_when_author_has_no_sessions(
        self, project: Path
    ) -> None:
        _write_session(
            project, "2026-03-01-1400.md", author=OTHER_EMAIL
        )

        result = latest_session(project, author=MOCK_EMAIL)

        assert result is None

    def test_latest_for_author_with_multiple_authors(
        self, project: Path
    ) -> None:
        _write_session(
            project,
            "2026-03-01-1000.md",
            author=MOCK_EMAIL,
            body="First by mock.",
        )
        _write_session(
            project,
            "2026-03-01-1200.md",
            author=OTHER_EMAIL,
            body="By other.",
        )
        _write_session(
            project,
            "2026-03-01-1400.md",
            author=MOCK_EMAIL,
            body="Second by mock.",
        )

        result = latest_session(project, author=MOCK_EMAIL)

        assert result is not None
        _, body = result
        assert "Second by mock." in body
