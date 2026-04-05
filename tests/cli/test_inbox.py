"""Tests for mantle.cli.inbox."""

from __future__ import annotations

import subprocess
import sys
from typing import TYPE_CHECKING

import pytest

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
    """Create a minimal .mantle/ with inbox/ directory."""
    (tmp_path / ".mantle" / "inbox").mkdir(parents=True)
    return tmp_path


# ── run_save_inbox_item ─────────────────────────────────────────


class TestRunSaveInboxItem:
    def test_run_save_inbox_item_success(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.inbox import run_save_inbox_item

        run_save_inbox_item(
            title="Add dark mode support",
            project_dir=project,
        )

        inbox_dir = project / ".mantle" / "inbox"
        files = list(inbox_dir.glob("*.md"))
        assert len(files) == 1

        captured = capsys.readouterr()
        assert "Add dark mode support" in captured.out
        assert "user" in captured.out
        assert files[0].name in captured.out

    def test_run_save_inbox_item_invalid_source(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.inbox import run_save_inbox_item

        with pytest.raises(SystemExit, match="1"):
            run_save_inbox_item(
                title="Some idea",
                source="invalid",
                project_dir=project,
            )

        captured = capsys.readouterr()
        assert "Error" in captured.out


# ── run_update_inbox_status ─────────────────────────────────────


class TestRunUpdateInboxStatus:
    def test_run_update_inbox_status_success(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.inbox import run_save_inbox_item, run_update_inbox_status

        run_save_inbox_item(
            title="Add dark mode support",
            project_dir=project,
        )

        inbox_dir = project / ".mantle" / "inbox"
        item_file = next(iter(inbox_dir.glob("*.md")))

        # Clear output from save
        capsys.readouterr()

        run_update_inbox_status(
            item=item_file.name,
            status="promoted",
            project_dir=project,
        )

        captured = capsys.readouterr()
        assert "Item updated" in captured.out
        assert item_file.name in captured.out
        assert "open" in captured.out
        assert "promoted" in captured.out

    def test_run_update_inbox_status_not_found(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.inbox import run_update_inbox_status

        with pytest.raises(SystemExit, match="1"):
            run_update_inbox_status(
                item="nonexistent.md",
                status="promoted",
                project_dir=project,
            )

        captured = capsys.readouterr()
        assert "Error" in captured.out

    def test_run_update_inbox_status_invalid_status(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.inbox import run_save_inbox_item, run_update_inbox_status

        run_save_inbox_item(
            title="Add dark mode support",
            project_dir=project,
        )

        inbox_dir = project / ".mantle" / "inbox"
        item_file = next(iter(inbox_dir.glob("*.md")))

        with pytest.raises(SystemExit, match="1"):
            run_update_inbox_status(
                item=item_file.name,
                status="invalid",
                project_dir=project,
            )

        captured = capsys.readouterr()
        assert "Error" in captured.out


# ── CLI wiring ──────────────────────────────────────────────────


class TestCLIWiring:
    def test_save_inbox_item_command_exists(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "mantle.cli.main",
                "save-inbox-item",
                "--help",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert "title" in result.stdout.lower()

    def test_update_inbox_status_command_exists(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "mantle.cli.main",
                "update-inbox-status",
                "--help",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert "item" in result.stdout.lower()
        assert "status" in result.stdout.lower()
