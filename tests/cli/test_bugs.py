"""Tests for mantle.cli.bugs."""

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
    """Create a minimal .mantle/ with bugs/ directory."""
    (tmp_path / ".mantle" / "bugs").mkdir(parents=True)
    return tmp_path


def _save_bug(
    project_dir: Path,
    **overrides: object,
) -> None:
    """Call run_save_bug with sensible defaults."""
    from mantle.cli.bugs import run_save_bug

    defaults: dict[str, object] = {
        "summary": "Compilation fails when no idea.md exists",
        "severity": "medium",
        "description": "The compiler crashes.",
        "reproduction": "Run mantle compile without idea.md.",
        "expected": "A helpful error message.",
        "actual": "An unhandled exception.",
        "project_dir": project_dir,
    }
    defaults.update(overrides)
    run_save_bug(**defaults)


# ── run_save_bug ────────────────────────────────────────────────


class TestRunSaveBug:
    def test_creates_file(self, project: Path) -> None:
        _save_bug(project)

        bugs_dir = project / ".mantle" / "bugs"
        files = list(bugs_dir.glob("*.md"))
        assert len(files) == 1

    def test_prints_confirmation(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _save_bug(project)
        captured = capsys.readouterr()

        assert "Bug captured" in captured.out
        assert "Compilation fails" in captured.out
        assert "medium" in captured.out

    def test_defaults_to_cwd(
        self,
        project: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.chdir(project)

        from mantle.cli.bugs import run_save_bug

        run_save_bug(
            summary="Test bug",
            severity="low",
            description="Desc.",
            reproduction="Steps.",
            expected="Expected.",
            actual="Actual.",
        )
        captured = capsys.readouterr()

        assert "Bug captured" in captured.out

    def test_handles_bug_exists_error(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _save_bug(project)

        with pytest.raises(SystemExit, match="1"):
            _save_bug(project)

        captured = capsys.readouterr()
        assert "already exists" in captured.out

    def test_handles_invalid_severity(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        with pytest.raises(SystemExit, match="1"):
            _save_bug(project, severity="critical")

        captured = capsys.readouterr()
        assert "Invalid severity" in captured.err


# ── run_update_bug_status ───────────────────────────────────────


class TestRunUpdateBugStatus:
    def test_updates_status(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.bugs import run_update_bug_status

        _save_bug(project)
        bugs_dir = project / ".mantle" / "bugs"
        bug_file = next(iter(bugs_dir.glob("*.md")))

        run_update_bug_status(
            bug=bug_file.name,
            status="fixed",
            project_dir=project,
        )
        captured = capsys.readouterr()

        assert "Bug updated" in captured.out
        assert "open" in captured.out
        assert "fixed" in captured.out

    def test_prints_fixed_by(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.bugs import run_update_bug_status

        _save_bug(project)
        bugs_dir = project / ".mantle" / "bugs"
        bug_file = next(iter(bugs_dir.glob("*.md")))

        run_update_bug_status(
            bug=bug_file.name,
            status="fixed",
            fixed_by="issue-21",
            project_dir=project,
        )
        captured = capsys.readouterr()

        assert "issue-21" in captured.out

    def test_handles_not_found(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.bugs import run_update_bug_status

        with pytest.raises(SystemExit, match="1"):
            run_update_bug_status(
                bug="nonexistent.md",
                status="fixed",
                project_dir=project,
            )

        captured = capsys.readouterr()
        assert "Bug not found" in captured.err

    def test_handles_invalid_status(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.bugs import run_update_bug_status

        _save_bug(project)
        bugs_dir = project / ".mantle" / "bugs"
        bug_file = next(iter(bugs_dir.glob("*.md")))

        with pytest.raises(SystemExit, match="1"):
            run_update_bug_status(
                bug=bug_file.name,
                status="invalid",
                project_dir=project,
            )

        captured = capsys.readouterr()
        assert "Invalid status" in captured.err


# ── CLI wiring ──────────────────────────────────────────────────


class TestCLIWiring:
    def test_save_bug_help(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "mantle.cli.main",
                "save-bug",
                "--help",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert "summary" in result.stdout.lower()
        assert "severity" in result.stdout.lower()

    def test_update_bug_status_help(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "mantle.cli.main",
                "update-bug-status",
                "--help",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert "bug" in result.stdout.lower()
        assert "status" in result.stdout.lower()
