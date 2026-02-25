"""Tests for mantle.cli.challenge."""

from __future__ import annotations

import subprocess
import sys
from datetime import date
from typing import TYPE_CHECKING

import pytest

from mantle.core import idea
from mantle.core.state import ProjectState, Status
from mantle.core.vault import write_note

if TYPE_CHECKING:
    from pathlib import Path

MOCK_EMAIL = "test@example.com"
TRANSCRIPT = "## Challenge Transcript\n\nQ: Why?\nA: Because."


@pytest.fixture(autouse=True)
def _mock_git(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock git identity for all tests in this module."""
    monkeypatch.setattr(
        "mantle.core.state.resolve_git_identity",
        lambda: MOCK_EMAIL,
    )


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """Create a minimal .mantle/ with state.md and idea.md."""
    (tmp_path / ".mantle").mkdir()
    (tmp_path / ".mantle" / "challenges").mkdir()
    _write_state(tmp_path)
    _write_idea(tmp_path)
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
        "Feedback loops are too slow"
        " — Persistent context eliminates ramp-up time\n\n"
        "## Current Focus\n\n"
        "Idea captured — run /mantle:challenge next.\n\n"
        "## Blockers\n\n"
        "_Anything preventing progress?_\n"
    )
    write_note(project_dir / ".mantle" / "state.md", st, body)


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
    write_note(project_dir / ".mantle" / "idea.md", note, body)


# ── run_save_challenge ──────────────────────────────────────────


class TestRunSaveChallenge:
    def test_prints_success(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.challenge import run_save_challenge

        run_save_challenge(
            transcript=TRANSCRIPT,
            project_dir=project,
        )
        captured = capsys.readouterr()

        assert "Challenge saved" in captured.out

    def test_prints_filename(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.challenge import run_save_challenge

        run_save_challenge(
            transcript=TRANSCRIPT,
            project_dir=project,
        )
        captured = capsys.readouterr()

        today = date.today().isoformat()
        assert f"{today}-challenge.md" in captured.out

    def test_prints_next_step(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.challenge import run_save_challenge

        run_save_challenge(
            transcript=TRANSCRIPT,
            project_dir=project,
        )
        captured = capsys.readouterr()

        assert "/mantle:design-product" in captured.out

    def test_warns_on_missing_idea(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        (tmp_path / ".mantle").mkdir()
        (tmp_path / ".mantle" / "challenges").mkdir()
        _write_state(tmp_path)

        from mantle.cli.challenge import run_save_challenge

        with pytest.raises(SystemExit, match="1"):
            run_save_challenge(
                transcript=TRANSCRIPT,
                project_dir=tmp_path,
            )

        captured = capsys.readouterr()
        assert "No idea.md found" in captured.out

    def test_defaults_to_cwd(
        self,
        project: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.chdir(project)

        from mantle.cli.challenge import run_save_challenge

        run_save_challenge(transcript=TRANSCRIPT)
        captured = capsys.readouterr()

        assert "Challenge saved" in captured.out


# ── CLI wiring ──────────────────────────────────────────────────


class TestCLIWiring:
    def test_save_challenge_help(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "mantle.cli.main",
                "save-challenge",
                "--help",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert "transcript" in result.stdout.lower()
