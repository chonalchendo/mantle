"""Tests for mantle.cli.scout."""

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
CONTENT = "## Scout\n\nAnalysis of the repository."
REPO_URL = "https://github.com/example/repo"
REPO_NAME = "example-repo"
DIMENSIONS = ["architecture", "testing"]


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
    (tmp_path / ".mantle" / "scouts").mkdir()
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


# -- run_save_scout -----------------------------------------------


class TestRunSaveScout:
    def test_run_save_scout_success(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.scout import run_save_scout

        run_save_scout(
            repo_url=REPO_URL,
            repo_name=REPO_NAME,
            dimensions=DIMENSIONS,
            content=CONTENT,
            project_dir=project,
        )
        captured = capsys.readouterr()

        assert "Scout report saved" in captured.out

        scouts = list(
            (project / ".mantle" / "scouts").glob("*.md")
        )
        assert len(scouts) == 1

    def test_run_save_scout_prints_confirmation(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.scout import run_save_scout

        run_save_scout(
            repo_url=REPO_URL,
            repo_name=REPO_NAME,
            dimensions=DIMENSIONS,
            content=CONTENT,
            project_dir=project,
        )
        captured = capsys.readouterr()

        assert REPO_NAME in captured.out
        assert str(len(DIMENSIONS)) in captured.out

    def test_run_save_scout_defaults_to_cwd(
        self,
        project: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.chdir(project)

        from mantle.cli.scout import run_save_scout

        run_save_scout(
            repo_url=REPO_URL,
            repo_name=REPO_NAME,
            dimensions=DIMENSIONS,
            content=CONTENT,
        )
        captured = capsys.readouterr()

        assert "Scout report saved" in captured.out

        scouts = list(
            (project / ".mantle" / "scouts").glob("*.md")
        )
        assert len(scouts) == 1

    def test_run_save_scout_invalid_raises_exit(
        self,
        project: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from mantle.cli.scout import run_save_scout

        monkeypatch.setattr(
            "mantle.core.scout.save_scout",
            lambda *a, **kw: (_ for _ in ()).throw(
                ValueError("bad input")
            ),
        )
        with pytest.raises(SystemExit) as exc_info:
            run_save_scout(
                repo_url=REPO_URL,
                repo_name=REPO_NAME,
                dimensions=DIMENSIONS,
                content=CONTENT,
                project_dir=project,
            )
        assert exc_info.value.code == 1


# -- CLI wiring ---------------------------------------------------


class TestCLIWiring:
    def test_save_scout_help(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "mantle.cli.main",
                "save-scout",
                "--help",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert "repo-url" in result.stdout.lower()
        assert "repo-name" in result.stdout.lower()
