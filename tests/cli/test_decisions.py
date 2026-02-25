"""Tests for mantle.cli.decisions."""

from __future__ import annotations

import subprocess
import sys
from datetime import date
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
    """Create a minimal .mantle/ with decisions dir."""
    (tmp_path / ".mantle").mkdir()
    (tmp_path / ".mantle" / "decisions").mkdir()
    return tmp_path


# ── run_save_decision ──────────────────────────────────────────


class TestRunSaveDecision:
    def test_prints_success(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.decisions import run_save_decision

        run_save_decision(
            topic="framework-selection",
            decision="Use FastAPI",
            alternatives=("Flask", "Django REST"),
            rationale="Best async support",
            reversal_trigger="Performance issues",
            confidence="8/10",
            reversible="medium",
            scope="system-design",
            project_dir=project,
        )
        captured = capsys.readouterr()

        assert "Decision saved" in captured.out

    def test_prints_topic(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.decisions import run_save_decision

        run_save_decision(
            topic="framework-selection",
            decision="Use FastAPI",
            alternatives=("Flask",),
            rationale="Best async support",
            reversal_trigger="Performance issues",
            confidence="8/10",
            reversible="medium",
            scope="system-design",
            project_dir=project,
        )
        captured = capsys.readouterr()

        assert "framework-selection" in captured.out

    def test_prints_filename(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.decisions import run_save_decision

        run_save_decision(
            topic="framework-selection",
            decision="Use FastAPI",
            alternatives=("Flask",),
            rationale="Best async support",
            reversal_trigger="Performance issues",
            confidence="8/10",
            reversible="medium",
            scope="system-design",
            project_dir=project,
        )
        captured = capsys.readouterr()

        today = date.today().isoformat()
        assert f"{today}-framework-selection.md" in captured.out

    def test_defaults_to_cwd(
        self,
        project: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.chdir(project)

        from mantle.cli.decisions import run_save_decision

        run_save_decision(
            topic="test-decision",
            decision="Test",
            alternatives=("A",),
            rationale="Because",
            reversal_trigger="Never",
            confidence="5/10",
            reversible="high",
            scope="system-design",
        )
        captured = capsys.readouterr()

        assert "Decision saved" in captured.out


# ── CLI wiring ──────────────────────────────────────────────────


class TestCLIWiring:
    def test_save_decision_help(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "mantle.cli.main",
                "save-decision",
                "--help",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert "topic" in result.stdout.lower()
        assert "decision" in result.stdout.lower()
        assert "alternatives" in result.stdout.lower()
        assert "rationale" in result.stdout.lower()
