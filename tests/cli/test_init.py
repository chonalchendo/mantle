"""Tests for mantle.cli.init."""

from __future__ import annotations

import subprocess
import sys
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from mantle.core.project import MANTLE_DIR

MOCK_EMAIL = "test@example.com"


@pytest.fixture(autouse=True)
def _mock_git(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock git identity for all tests in this module."""
    monkeypatch.setattr(
        "mantle.core.state.resolve_git_identity",
        lambda: MOCK_EMAIL,
    )


# ── run_init ─────────────────────────────────────────────────────


class TestRunInit:
    def test_idempotency_warns(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        (tmp_path / MANTLE_DIR).mkdir()

        from mantle.cli.init import run_init

        run_init(tmp_path)
        captured = capsys.readouterr()

        assert "already exists" in captured.out

    def test_idempotency_preserves_files(self, tmp_path: Path) -> None:
        mantle_path = tmp_path / MANTLE_DIR
        mantle_path.mkdir()
        marker = mantle_path / "custom.md"
        marker.write_text("user content")

        from mantle.cli.init import run_init

        run_init(tmp_path)

        assert marker.read_text() == "user content"

    def test_creates_mantle_directory(self, tmp_path: Path) -> None:
        from mantle.cli.init import run_init

        run_init(tmp_path)

        assert (tmp_path / MANTLE_DIR).is_dir()

    def test_derives_project_name(self, tmp_path: Path) -> None:
        from mantle.cli.init import run_init

        run_init(tmp_path)

        from mantle.core.state import ProjectState
        from mantle.core.vault import read_note

        state_path = tmp_path / MANTLE_DIR / "state.md"
        note = read_note(state_path, ProjectState)
        assert note.frontmatter.project == tmp_path.name


# ── Onboarding message ───────────────────────────────────────────


class TestOnboarding:
    def test_mentions_idea_command(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.init import run_init

        run_init(tmp_path)
        captured = capsys.readouterr()

        assert "/mantle:idea" in captured.out

    def test_mentions_help_command(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.init import run_init

        run_init(tmp_path)
        captured = capsys.readouterr()

        assert "/mantle:help" in captured.out

    def test_mentions_init_vault(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.init import run_init

        run_init(tmp_path)
        captured = capsys.readouterr()

        assert "init-vault" in captured.out


# ── CLI wiring ───────────────────────────────────────────────────


class TestCLIWiring:
    def test_init_help(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "mantle.cli.main", "init", "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert "init" in result.stdout.lower()
