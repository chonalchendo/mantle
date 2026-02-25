"""Tests for mantle.cli.idea."""

from __future__ import annotations

import subprocess
import sys
from typing import TYPE_CHECKING

import pytest

from mantle.core.state import ProjectState, Status
from mantle.core.vault import write_note

if TYPE_CHECKING:
    from pathlib import Path

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
    """Create a minimal .mantle/ with state.md."""
    from datetime import date

    (tmp_path / ".mantle").mkdir()
    state = ProjectState(
        project="test-project",
        status=Status.IDEA,
        created=date(2025, 1, 1),
        created_by=MOCK_EMAIL,
        updated=date(2025, 1, 1),
        updated_by=MOCK_EMAIL,
    )
    body = (
        "## Summary\n\n"
        "_Describe the project in one or two sentences._\n\n"
        "## Current Focus\n\n"
        "_What are you working on right now?_\n"
    )
    write_note(tmp_path / ".mantle" / "state.md", state, body)
    return tmp_path


# ── run_save_idea ────────────────────────────────────────────────


class TestRunSaveIdea:
    def test_prints_success(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.idea import run_save_idea

        run_save_idea(
            problem="Feedback loops are too slow",
            insight="Persistent context eliminates ramp-up",
            target_user="Developers",
            success_criteria=("Ship in 2 weeks",),
            project_dir=project,
        )
        captured = capsys.readouterr()

        assert "Idea captured" in captured.out

    def test_prints_problem_and_insight(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.idea import run_save_idea

        run_save_idea(
            problem="Feedback loops are too slow",
            insight="Persistent context eliminates ramp-up",
            target_user="Developers",
            success_criteria=("Ship in 2 weeks",),
            project_dir=project,
        )
        captured = capsys.readouterr()

        assert "Feedback loops are too slow" in captured.out
        assert "Persistent context eliminates ramp-up" in captured.out

    def test_prints_criteria_count(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.idea import run_save_idea

        run_save_idea(
            problem="Test",
            insight="Test insight",
            target_user="Devs",
            success_criteria=("a", "b", "c"),
            project_dir=project,
        )
        captured = capsys.readouterr()

        assert "3" in captured.out

    def test_prints_next_step(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.idea import run_save_idea

        run_save_idea(
            problem="Test",
            insight="Test insight",
            target_user="Devs",
            success_criteria=("a",),
            project_dir=project,
        )
        captured = capsys.readouterr()

        assert "/mantle:challenge" in captured.out

    def test_warns_on_existing(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.idea import run_save_idea

        run_save_idea(
            problem="First",
            insight="First insight",
            target_user="Devs",
            success_criteria=("a",),
            project_dir=project,
        )

        with pytest.raises(SystemExit, match="1"):
            run_save_idea(
                problem="Second",
                insight="Second insight",
                target_user="Devs",
                success_criteria=("a",),
                project_dir=project,
            )

        captured = capsys.readouterr()
        assert "already exists" in captured.out

    def test_overwrite_succeeds(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.idea import run_save_idea

        run_save_idea(
            problem="First",
            insight="First insight",
            target_user="Devs",
            success_criteria=("a",),
            project_dir=project,
        )
        run_save_idea(
            problem="Second",
            insight="Second insight",
            target_user="Devs",
            success_criteria=("a",),
            overwrite=True,
            project_dir=project,
        )

        from mantle.core.idea import load_idea

        loaded = load_idea(project)
        assert loaded.problem == "Second"

    def test_defaults_to_cwd(
        self,
        project: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.chdir(project)

        from mantle.cli.idea import run_save_idea

        run_save_idea(
            problem="Test",
            insight="Test insight",
            target_user="Devs",
            success_criteria=("a",),
        )
        captured = capsys.readouterr()

        assert "Idea captured" in captured.out


# ── CLI wiring ───────────────────────────────────────────────────


class TestCLIWiring:
    def test_save_idea_help(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "mantle.cli.main",
                "save-idea",
                "--help",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert "problem" in result.stdout.lower()
        assert "insight" in result.stdout.lower()
