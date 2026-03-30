"""Tests for mantle.core.bugs."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

import pydantic
import pytest

if TYPE_CHECKING:
    from pathlib import Path

from mantle.core import bugs
from mantle.core.bugs import (
    BugExistsError,
    BugNote,
)

MOCK_EMAIL = "test@example.com"


@pytest.fixture(autouse=True)
def _mock_git(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock git identity for all tests in this module."""
    monkeypatch.setattr(
        "mantle.core.state.resolve_git_identity",
        lambda: MOCK_EMAIL,
    )


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """Create a minimal .mantle/ with bugs/ directory."""
    (tmp_path / ".mantle" / "bugs").mkdir(parents=True)
    return tmp_path


def _create_bug(
    project_dir: Path,
    **overrides: object,
) -> tuple[BugNote, Path]:
    """Create a bug with sensible defaults."""
    defaults: dict[str, object] = {
        "summary": "Compilation fails when no idea.md exists",
        "severity": "medium",
        "description": "The compiler crashes with a traceback.",
        "reproduction": "Run mantle compile without idea.md.",
        "expected": "A helpful error message.",
        "actual": "An unhandled exception.",
    }
    defaults.update(overrides)
    return bugs.create_bug(project_dir, **defaults)


# ── BugNote model ───────────────────────────────────────────────


class TestBugNote:
    def test_frozen(self) -> None:
        note = BugNote(
            date=date.today(),
            author="a@b.com",
            summary="Test bug",
            severity="medium",
        )

        with pytest.raises(pydantic.ValidationError):
            note.summary = "Changed"  # type: ignore[misc]

    def test_default_status_is_open(self) -> None:
        note = BugNote(
            date=date.today(),
            author="a@b.com",
            summary="Test bug",
            severity="medium",
        )

        assert note.status == "open"

    def test_default_tags(self) -> None:
        note = BugNote(
            date=date.today(),
            author="a@b.com",
            summary="Test bug",
            severity="medium",
        )

        assert "type/bug" in note.tags
        assert "status/open" in note.tags

    def test_related_issue_defaults_to_none(self) -> None:
        note = BugNote(
            date=date.today(),
            author="a@b.com",
            summary="Test bug",
            severity="medium",
        )

        assert note.related_issue is None

    def test_related_files_defaults_to_empty(self) -> None:
        note = BugNote(
            date=date.today(),
            author="a@b.com",
            summary="Test bug",
            severity="medium",
        )

        assert note.related_files == ()

    def test_fixed_by_defaults_to_none(self) -> None:
        note = BugNote(
            date=date.today(),
            author="a@b.com",
            summary="Test bug",
            severity="medium",
        )

        assert note.fixed_by is None


# ── create_bug ──────────────────────────────────────────────────


class TestCreateBug:
    def test_writes_file(self, project: Path) -> None:
        _, path = _create_bug(project)

        assert path.exists()

    def test_filename_matches_pattern(self, project: Path) -> None:
        _, path = _create_bug(project)

        today = str(date.today())
        assert path.name.startswith(today)
        assert path.name.endswith(".md")
        assert path.parent.name == "bugs"

    def test_correct_frontmatter(self, project: Path) -> None:
        note, _ = _create_bug(project)

        assert note.date == date.today()
        assert note.author == MOCK_EMAIL
        assert note.summary == ("Compilation fails when no idea.md exists")
        assert note.severity == "medium"
        assert note.status == "open"
        assert note.related_issue is None
        assert note.related_files == ()
        assert note.fixed_by is None

    def test_round_trip_frontmatter(self, project: Path) -> None:
        created, path = _create_bug(project)
        loaded, _ = bugs.load_bug(path)

        assert loaded.date == created.date
        assert loaded.author == created.author
        assert loaded.summary == created.summary
        assert loaded.severity == created.severity
        assert loaded.status == created.status
        assert loaded.tags == created.tags

    def test_round_trip_body(self, project: Path) -> None:
        _, path = _create_bug(project)
        _, body = bugs.load_bug(path)

        assert "## Description" in body
        assert "The compiler crashes" in body
        assert "## Reproduction" in body
        assert "Run mantle compile" in body
        assert "## Expected Behaviour" in body
        assert "A helpful error message" in body
        assert "## Actual Behaviour" in body
        assert "An unhandled exception" in body

    def test_stamps_author(self, project: Path) -> None:
        note, _ = _create_bug(project)

        assert note.author == MOCK_EMAIL

    def test_tags_include_severity(self, project: Path) -> None:
        note, _ = _create_bug(project)

        assert "severity/medium" in note.tags

    def test_raises_on_invalid_severity(self, project: Path) -> None:
        with pytest.raises(ValueError, match="Invalid severity"):
            _create_bug(project, severity="critical")

    def test_raises_on_existing(self, project: Path) -> None:
        _create_bug(project)

        with pytest.raises(BugExistsError):
            _create_bug(project)

    def test_slugifies_summary(self, project: Path) -> None:
        _, path = _create_bug(
            project,
            summary="Button colour is wrong",
        )

        assert "button-colour-is-wrong" in path.name

    def test_truncates_slug(self, project: Path) -> None:
        long_summary = "a " * 50  # 100 chars before slugify
        _, path = _create_bug(project, summary=long_summary)

        # Filename = date + "-" + slug + ".md"
        slug = path.stem.split("-", 3)[-1]  # Skip YYYY-MM-DD
        assert len(slug) <= 30

    def test_related_issue_optional(self, project: Path) -> None:
        note, _ = _create_bug(
            project,
            related_issue="issue-08",
        )

        assert note.related_issue == "issue-08"

    def test_related_files_optional(self, project: Path) -> None:
        note, _ = _create_bug(
            project,
            related_files=("src/foo.py", "src/bar.py"),
        )

        assert note.related_files == ("src/foo.py", "src/bar.py")


# ── load_bug ────────────────────────────────────────────────────


class TestLoadBug:
    def test_reads_saved(self, project: Path) -> None:
        _, path = _create_bug(project)
        loaded, _ = bugs.load_bug(path)

        assert loaded.summary == ("Compilation fails when no idea.md exists")

    def test_file_not_found(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            bugs.load_bug(tmp_path / "nonexistent.md")


# ── list_bugs ───────────────────────────────────────────────────


class TestListBugs:
    def test_empty_when_no_bugs(self, project: Path) -> None:
        result = bugs.list_bugs(project)

        assert result == []

    def test_returns_sorted_paths(self, project: Path) -> None:
        _create_bug(project, summary="First bug")
        _create_bug(project, summary="Second bug")

        result = bugs.list_bugs(project)

        assert len(result) == 2
        assert result[0].name < result[1].name

    def test_filters_by_status(self, project: Path) -> None:
        _create_bug(project, summary="Open bug")
        _create_bug(project, summary="Fixed bug")
        bugs.update_bug_status(
            project,
            bugs.list_bugs(project)[1].name,
            status="fixed",
        )

        open_bugs = bugs.list_bugs(project, status="open")
        fixed_bugs = bugs.list_bugs(project, status="fixed")

        assert len(open_bugs) == 1
        assert len(fixed_bugs) == 1

    def test_returns_all_when_no_status(self, project: Path) -> None:
        _create_bug(project, summary="Bug one")
        _create_bug(project, summary="Bug two")

        result = bugs.list_bugs(project, status=None)

        assert len(result) == 2

    def test_returns_empty_when_dir_missing(self, tmp_path: Path) -> None:
        result = bugs.list_bugs(tmp_path)

        assert result == []


# ── update_bug_status ───────────────────────────────────────────


class TestUpdateBugStatus:
    def test_changes_status(self, project: Path) -> None:
        _, path = _create_bug(project)
        updated, _ = bugs.update_bug_status(project, path.name, status="fixed")

        assert updated.status == "fixed"

    def test_returns_old_status(self, project: Path) -> None:
        _, path = _create_bug(project)
        _, old_status = bugs.update_bug_status(
            project, path.name, status="fixed"
        )

        assert old_status == "open"

    def test_sets_fixed_by(self, project: Path) -> None:
        _, path = _create_bug(project)
        updated, _ = bugs.update_bug_status(
            project,
            path.name,
            status="fixed",
            fixed_by="issue-21",
        )

        assert updated.fixed_by == "issue-21"

    def test_updates_tags(self, project: Path) -> None:
        _, path = _create_bug(project)
        updated, _ = bugs.update_bug_status(project, path.name, status="fixed")

        assert "status/fixed" in updated.tags
        assert "status/open" not in updated.tags

    def test_file_not_found(self, project: Path) -> None:
        with pytest.raises(FileNotFoundError, match="Bug not found"):
            bugs.update_bug_status(project, "nonexistent.md", status="fixed")

    def test_invalid_status(self, project: Path) -> None:
        _, path = _create_bug(project)

        with pytest.raises(ValueError, match="Invalid status"):
            bugs.update_bug_status(project, path.name, status="invalid")

    def test_preserves_other_fields(self, project: Path) -> None:
        _, path = _create_bug(
            project,
            related_issue="issue-08",
            related_files=("src/foo.py",),
        )
        updated, _ = bugs.update_bug_status(project, path.name, status="fixed")

        assert updated.summary == ("Compilation fails when no idea.md exists")
        assert updated.severity == "medium"
        assert updated.related_issue == "issue-08"
        assert updated.related_files == ("src/foo.py",)

    def test_wont_fix_status(self, project: Path) -> None:
        _, path = _create_bug(project)
        updated, _ = bugs.update_bug_status(
            project, path.name, status="wont-fix"
        )

        assert updated.status == "wont-fix"
        assert "status/wont-fix" in updated.tags
