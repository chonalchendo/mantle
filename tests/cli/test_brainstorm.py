"""Tests for mantle.cli.brainstorm."""

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
CONTENT = "## Brainstorm\n\nShould we add a plugin system?"


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
    (tmp_path / ".mantle" / "brainstorms").mkdir()
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
        "Feedback loops are too slow"
        " — Persistent context eliminates ramp-up time\n\n"
        "## Current Focus\n\n"
        "Idea captured — run /mantle:challenge next.\n\n"
        "## Blockers\n\n"
        "_Anything preventing progress?_\n"
    )
    write_note(project_dir / ".mantle" / "state.md", st, body)


# -- run_save_brainstorm ------------------------------------------


class TestRunSaveBrainstorm:
    def test_save_brainstorm_cli_success(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.brainstorm import run_save_brainstorm

        run_save_brainstorm(
            title="Plugin system",
            verdict="proceed",
            content=CONTENT,
            project_dir=project,
        )
        captured = capsys.readouterr()

        assert "Brainstorm saved" in captured.out

        # Verify file exists.
        brainstorms = list(
            (project / ".mantle" / "brainstorms").glob("*.md")
        )
        assert len(brainstorms) == 1

    def test_save_brainstorm_cli_invalid_verdict(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.brainstorm import run_save_brainstorm

        with pytest.raises(SystemExit, match="1"):
            run_save_brainstorm(
                title="Plugin system",
                verdict="maybe",
                content=CONTENT,
                project_dir=project,
            )

        captured = capsys.readouterr()
        assert "Error" in captured.out

    def test_save_brainstorm_cli_default_cwd(
        self,
        project: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.chdir(project)

        from mantle.cli.brainstorm import run_save_brainstorm

        run_save_brainstorm(
            title="Plugin system",
            verdict="research",
            content=CONTENT,
        )
        captured = capsys.readouterr()

        assert "Brainstorm saved" in captured.out

        brainstorms = list(
            (project / ".mantle" / "brainstorms").glob("*.md")
        )
        assert len(brainstorms) == 1

    def test_prints_filename(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.brainstorm import run_save_brainstorm

        run_save_brainstorm(
            title="Plugin system",
            verdict="proceed",
            content=CONTENT,
            project_dir=project,
        )
        captured = capsys.readouterr()

        today = date.today().isoformat()
        assert f"{today}-plugin-system.md" in captured.out

    def test_prints_verdict_next_proceed(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.brainstorm import run_save_brainstorm

        run_save_brainstorm(
            title="Plugin system",
            verdict="proceed",
            content=CONTENT,
            project_dir=project,
        )
        captured = capsys.readouterr()

        assert "/mantle:add-issue" in captured.out

    def test_prints_verdict_next_research(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.brainstorm import run_save_brainstorm

        run_save_brainstorm(
            title="Plugin system",
            verdict="research",
            content=CONTENT,
            project_dir=project,
        )
        captured = capsys.readouterr()

        assert "/mantle:research" in captured.out

    def test_prints_verdict_next_scrap(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.brainstorm import run_save_brainstorm

        run_save_brainstorm(
            title="Plugin system",
            verdict="scrap",
            content=CONTENT,
            project_dir=project,
        )
        captured = capsys.readouterr()

        assert "scrapped" in captured.out


# -- CLI wiring ---------------------------------------------------


class TestCLIWiring:
    def test_save_brainstorm_help(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "mantle.cli.main",
                "save-brainstorm",
                "--help",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert "title" in result.stdout.lower()
        assert "verdict" in result.stdout.lower()
