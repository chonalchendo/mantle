"""Tests for mantle.cli.issues."""

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


@pytest.fixture(autouse=True)
def _mock_git(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock git identity for all tests in this module."""
    monkeypatch.setattr(
        "mantle.core.state.resolve_git_identity",
        lambda: MOCK_EMAIL,
    )


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """Create a minimal .mantle/ with state.md and issues dir."""
    (tmp_path / ".mantle").mkdir()
    (tmp_path / ".mantle" / "issues").mkdir()
    state = ProjectState(
        project="test-project",
        status=Status.SYSTEM_DESIGN,
        created=date(2025, 1, 1),
        created_by=MOCK_EMAIL,
        updated=date(2025, 1, 1),
        updated_by=MOCK_EMAIL,
    )
    body = (
        "## Summary\n\n"
        "Test project\n\n"
        "## Current Focus\n\n"
        "Designing the system.\n\n"
        "## Blockers\n\n"
        "_Anything preventing progress?_\n"
    )
    write_note(tmp_path / ".mantle" / "state.md", state, body)
    return tmp_path


# ── run_save_issue ──────────────────────────────────────────────


class TestRunSaveIssue:
    def test_creates_issue_file(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.issues import run_save_issue

        run_save_issue(
            title="Context engine",
            slice=("core", "tests"),
            content="## What to build\n\nBuild it.\n",
            project_dir=project,
        )

        assert (
            project / ".mantle" / "issues" / "issue-01-context-engine.md"
        ).exists()

    def test_prints_confirmation(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.issues import run_save_issue

        run_save_issue(
            title="Context engine",
            slice=("core", "tests"),
            content="## What to build\n\nBuild it.\n",
            project_dir=project,
        )
        captured = capsys.readouterr()

        assert "issue-01-context-engine.md" in captured.out
        assert "Context engine" in captured.out

    def test_prints_slice(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.issues import run_save_issue

        run_save_issue(
            title="Context engine",
            slice=("core", "tests"),
            content="## What to build\n\nBuild it.\n",
            project_dir=project,
        )
        captured = capsys.readouterr()

        assert "core, tests" in captured.out

    def test_prints_blocked_by(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.issues import run_save_issue

        run_save_issue(
            title="Context engine",
            slice=("core",),
            content="Build it.\n",
            blocked_by=(2, 5),
            project_dir=project,
        )
        captured = capsys.readouterr()

        assert "Blocked by:" in captured.out
        assert "issue-02" in captured.out
        assert "issue-05" in captured.out

    def test_omits_blocked_by_when_empty(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.issues import run_save_issue

        run_save_issue(
            title="Context engine",
            slice=("core",),
            content="Build it.\n",
            project_dir=project,
        )
        captured = capsys.readouterr()

        assert "Blocked by:" not in captured.out

    def test_passes_skills_required_to_save_issue(
        self,
        project: Path,
    ) -> None:
        from mantle.cli.issues import run_save_issue
        from mantle.core import issues as core_issues

        run_save_issue(
            title="Context engine",
            slice=("core",),
            content="Build it.\n",
            skills_required=("google-python-style", "pytest"),
            project_dir=project,
        )

        issue_path = (
            project / ".mantle" / "issues" / "issue-01-context-engine.md"
        )
        note, _ = core_issues.load_issue(issue_path)
        assert note.skills_required == ("google-python-style", "pytest")

    def test_defaults_to_cwd(
        self,
        project: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.chdir(project)

        from mantle.cli.issues import run_save_issue

        run_save_issue(
            title="Context engine",
            slice=("core",),
            content="Build it.\n",
        )
        captured = capsys.readouterr()

        assert "issue-01-context-engine.md" in captured.out

    def test_handles_issue_exists_error(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.issues import run_save_issue

        run_save_issue(
            title="First",
            slice=("core",),
            content="Build it.\n",
            project_dir=project,
        )

        with pytest.raises(SystemExit, match="1"):
            run_save_issue(
                title="Second",
                slice=("core",),
                content="Build it again.\n",
                issue=1,
                project_dir=project,
            )

        captured = capsys.readouterr()
        assert "already exists" in captured.out

    def test_handles_invalid_transition(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        (tmp_path / ".mantle").mkdir()
        (tmp_path / ".mantle" / "issues").mkdir()
        state = ProjectState(
            project="test-project",
            status=Status.IDEA,
            created=date(2025, 1, 1),
            created_by=MOCK_EMAIL,
            updated=date(2025, 1, 1),
            updated_by=MOCK_EMAIL,
        )
        body = (
            "## Summary\n\nTest\n\n"
            "## Current Focus\n\nIdea phase.\n\n"
            "## Blockers\n\nNone.\n"
        )
        write_note(tmp_path / ".mantle" / "state.md", state, body)

        from mantle.cli.issues import run_save_issue

        with pytest.raises(SystemExit, match="1"):
            run_save_issue(
                title="Test",
                slice=("core",),
                content="Build it.\n",
                project_dir=tmp_path,
            )

        captured = capsys.readouterr()
        assert "Cannot plan issues" in captured.out


# ── run_set_slices ──────────────────────────────────────────────


class TestRunSetSlices:
    def test_updates_slices(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.issues import run_set_slices

        run_set_slices(
            slices=("core", "cli", "tests"),
            project_dir=project,
        )

        from mantle.core.state import load_state

        loaded = load_state(project)
        assert loaded.slices == ("core", "cli", "tests")

    def test_prints_confirmation(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.issues import run_set_slices

        run_set_slices(
            slices=("ingestion", "transformation", "api", "storage"),
            project_dir=project,
        )
        captured = capsys.readouterr()

        assert "Project slices defined (4)" in captured.out
        assert "ingestion, transformation, api, storage" in captured.out

    def test_defaults_to_cwd(
        self,
        project: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.chdir(project)

        from mantle.cli.issues import run_set_slices

        run_set_slices(slices=("core",))
        captured = capsys.readouterr()

        assert "Project slices defined" in captured.out


# ── CLI wiring ──────────────────────────────────────────────────


class TestCLIWiring:
    def test_save_issue_help(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "mantle.cli.main",
                "save-issue",
                "--help",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert "title" in result.stdout.lower()
        assert "slice" in result.stdout.lower()

    def test_save_issue_help_mentions_skills_required(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "mantle.cli.main",
                "save-issue",
                "--help",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert "skills-required" in result.stdout

    def test_set_slices_help(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "mantle.cli.main",
                "set-slices",
                "--help",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert "slice" in result.stdout.lower()
