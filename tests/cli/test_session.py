"""Tests for mantle.cli.session."""

from __future__ import annotations

import subprocess
import sys
from datetime import date
from typing import TYPE_CHECKING

import pytest

from mantle.core.state import ProjectState, Status
from mantle.core.vault import write_note

if TYPE_CHECKING:
    from pathlib import Path

MOCK_EMAIL = "test@example.com"
BODY = (
    "## Summary\n\n"
    "Implemented session logging.\n\n"
    "## What Was Done\n\n"
    "- Added core session module\n\n"
    "## Decisions Made\n\n"
    "None\n\n"
    "## What's Next\n\n"
    "- Add CLI command\n\n"
    "## Open Questions\n\n"
    "None\n"
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
    """Create a minimal .mantle/ with state.md."""
    (tmp_path / ".mantle").mkdir()
    (tmp_path / ".mantle" / "sessions").mkdir()
    _write_state(tmp_path)
    return tmp_path


def _write_state(project_dir: Path) -> None:
    """Write a state.md for testing."""
    st = ProjectState(
        project="test-project",
        status=Status.IDEA,
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
    write_note(project_dir / ".mantle" / "state.md", st, body)


# ── run_save_session ─────────────────────────────────────────────


class TestRunSaveSession:
    def test_prints_success(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.session import run_save_session

        run_save_session(
            content=BODY,
            commands_used=("idea",),
            project_dir=project,
        )
        captured = capsys.readouterr()

        assert "Session log saved" in captured.out

    def test_creates_file(self, project: Path) -> None:
        from mantle.cli.session import run_save_session

        run_save_session(
            content=BODY,
            commands_used=("idea",),
            project_dir=project,
        )

        sessions = list((project / ".mantle" / "sessions").glob("*.md"))
        assert len(sessions) == 1

    def test_prints_word_count(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.session import run_save_session

        run_save_session(
            content=BODY,
            project_dir=project,
        )
        captured = capsys.readouterr()

        assert "Words:" in captured.out

    def test_warns_on_long_body(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.session import run_save_session

        long_body = " ".join(["word"] * 300)
        run_save_session(
            content=long_body,
            project_dir=project,
        )
        captured = capsys.readouterr()

        assert "Warning:" in captured.out


# ── _extract_summary ──────────────────────────────────────────────


class TestExtractSummary:
    def test_extracts_first_line_after_summary_heading(self) -> None:
        from mantle.cli.session import _extract_summary

        content = (
            "## Summary\n\n"
            "Implemented the build pipeline.\n\n"
            "## What Was Done\n"
        )
        assert _extract_summary(content) == "Implemented the build pipeline."

    def test_fallback_when_no_summary(self) -> None:
        from mantle.cli.session import _extract_summary

        assert _extract_summary("Just some text.") == "update artifacts"

    def test_truncates_long_summary(self) -> None:
        from mantle.cli.session import _extract_summary

        content = "## Summary\n\n" + "a" * 100 + "\n"
        result = _extract_summary(content)
        assert len(result) <= 72


# ── _auto_commit ──────────────────────────────────────────────────


class TestAutoCommit:
    @pytest.fixture
    def git_project(self, tmp_path: Path) -> Path:
        """Create a project with a git repo."""
        subprocess.run(
            ["git", "init"], cwd=tmp_path, capture_output=True
        )
        subprocess.run(
            ["git", "config", "user.email", MOCK_EMAIL],
            cwd=tmp_path,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=tmp_path,
            capture_output=True,
        )
        (tmp_path / ".mantle").mkdir()
        (tmp_path / ".mantle" / "sessions").mkdir()
        _write_state(tmp_path)
        # Initial commit so we can make further commits
        subprocess.run(
            ["git", "add", "."], cwd=tmp_path, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", "init"],
            cwd=tmp_path,
            capture_output=True,
        )
        return tmp_path

    def test_commits_mantle_changes(self, git_project: Path) -> None:
        from mantle.cli.session import _auto_commit

        # Create an uncommitted file
        (git_project / ".mantle" / "issues").mkdir(exist_ok=True)
        (git_project / ".mantle" / "issues" / "issue-01-test-issue.md").write_text(
            "test"
        )

        _auto_commit(git_project, "plan-issues", "planned 3 issues")

        result = subprocess.run(
            ["git", "log", "--oneline", "-1"],
            cwd=git_project,
            capture_output=True,
            text=True,
        )
        assert "chore(mantle): plan-issues" in result.stdout

    def test_no_commit_when_clean(self, git_project: Path) -> None:
        from mantle.cli.session import _auto_commit

        # Get current commit count
        before = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            cwd=git_project,
            capture_output=True,
            text=True,
        )

        _auto_commit(git_project, "idea", "test")

        after = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            cwd=git_project,
            capture_output=True,
            text=True,
        )
        assert before.stdout == after.stdout


# ── CLI wiring ───────────────────────────────────────────────────


class TestCLIWiring:
    def test_save_session_help(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "mantle.cli.main",
                "save-session",
                "--help",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert "content" in result.stdout.lower()
