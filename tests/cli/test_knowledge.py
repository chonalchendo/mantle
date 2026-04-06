"""Tests for mantle.cli.knowledge."""

from __future__ import annotations

import subprocess
import sys
from datetime import date
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

MOCK_EMAIL = "test@example.com"
CONTENT = "## Distillation\n\nSynthesized knowledge about TDD."


@pytest.fixture(autouse=True)
def _mock_git(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock git identity for all tests in this module."""
    monkeypatch.setattr(
        "mantle.core.state.resolve_git_identity",
        lambda: MOCK_EMAIL,
    )


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """Create a minimal .mantle/ with distillations dir."""
    (tmp_path / ".mantle").mkdir()
    (tmp_path / ".mantle" / "distillations").mkdir()
    return tmp_path


# -- run_save_distillation ----------------------------------------


class TestRunSaveDistillation:
    def test_save_distillation_command(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.knowledge import run_save_distillation

        run_save_distillation(
            topic="TDD practices",
            source_paths=["notes/a.md", "notes/b.md"],
            content=CONTENT,
            project_dir=project,
        )
        captured = capsys.readouterr()

        assert "saved" in captured.out.lower()

        distillations = list(
            (project / ".mantle" / "distillations").glob("*.md")
        )
        assert len(distillations) == 1

    def test_save_distillation_command_prints_topic(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.knowledge import run_save_distillation

        run_save_distillation(
            topic="TDD practices",
            source_paths=["notes/a.md"],
            content=CONTENT,
            project_dir=project,
        )
        captured = capsys.readouterr()

        assert "TDD practices" in captured.out

    def test_save_distillation_command_prints_source_count(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.knowledge import run_save_distillation

        run_save_distillation(
            topic="TDD practices",
            source_paths=["notes/a.md", "notes/b.md"],
            content=CONTENT,
            project_dir=project,
        )
        captured = capsys.readouterr()

        assert "2" in captured.out

    def test_save_distillation_command_prints_filename(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.knowledge import run_save_distillation

        run_save_distillation(
            topic="TDD practices",
            source_paths=["notes/a.md"],
            content=CONTENT,
            project_dir=project,
        )
        captured = capsys.readouterr()

        today = date.today().isoformat()
        assert f"{today}-tdd-practices.md" in captured.out

    def test_save_distillation_command_invalid(
        self,
        capsys: pytest.CaptureFixture[str],
        tmp_path: Path,
    ) -> None:
        """Missing required --topic causes ValueError -> SystemExit."""
        from mantle.cli.knowledge import run_save_distillation

        # topic is empty string — knowledge.save_distillation raises ValueError
        with pytest.raises((SystemExit, ValueError)):
            run_save_distillation(
                topic="",
                source_paths=[],
                content=CONTENT,
                project_dir=tmp_path,
            )


# -- run_list_distillations ---------------------------------------


class TestRunListDistillations:
    def test_list_distillations_command_empty(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.knowledge import run_list_distillations

        run_list_distillations(project_dir=project)
        captured = capsys.readouterr()

        assert "0 distillation(s)" in captured.out

    def test_list_distillations_command_with_items(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.knowledge import (
            run_list_distillations,
            run_save_distillation,
        )

        run_save_distillation(
            topic="TDD practices",
            source_paths=["notes/a.md"],
            content=CONTENT,
            project_dir=project,
        )
        run_save_distillation(
            topic="Clean architecture",
            source_paths=["notes/b.md"],
            content=CONTENT,
            project_dir=project,
        )

        capsys.readouterr()  # discard save output
        run_list_distillations(project_dir=project)
        captured = capsys.readouterr()

        assert "2 distillation(s)" in captured.out
        assert "TDD practices" in captured.out
        assert "Clean architecture" in captured.out

    def test_list_distillations_command_topic_filter(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.knowledge import (
            run_list_distillations,
            run_save_distillation,
        )

        run_save_distillation(
            topic="TDD practices",
            source_paths=["notes/a.md"],
            content=CONTENT,
            project_dir=project,
        )
        run_save_distillation(
            topic="Clean architecture",
            source_paths=["notes/b.md"],
            content=CONTENT,
            project_dir=project,
        )

        capsys.readouterr()  # discard save output
        run_list_distillations(topic="TDD", project_dir=project)
        captured = capsys.readouterr()

        assert "1 distillation(s)" in captured.out
        assert "TDD practices" in captured.out
        assert "Clean architecture" not in captured.out
        assert "filtered by: TDD" in captured.out


# -- run_load_distillation ----------------------------------------


class TestRunLoadDistillation:
    def test_load_distillation_command(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.knowledge import (
            run_load_distillation,
            run_save_distillation,
        )
        from mantle.core import knowledge

        run_save_distillation(
            topic="TDD practices",
            source_paths=["notes/a.md", "notes/b.md"],
            content=CONTENT,
            project_dir=project,
        )
        paths = knowledge.list_distillations(project)
        assert len(paths) == 1

        capsys.readouterr()  # discard save output
        run_load_distillation(
            path=str(paths[0]),
            project_dir=project,
        )
        captured = capsys.readouterr()

        assert "TDD practices" in captured.out
        assert "Distillation" in captured.out


# -- CLI wiring ---------------------------------------------------


class TestCLIWiring:
    def test_save_distillation_help(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "mantle.cli.main",
                "save-distillation",
                "--help",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert "topic" in result.stdout.lower()

    def test_list_distillations_help(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "mantle.cli.main",
                "list-distillations",
                "--help",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0

    def test_load_distillation_help(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "mantle.cli.main",
                "load-distillation",
                "--help",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
