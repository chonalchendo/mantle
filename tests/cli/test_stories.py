"""Tests for mantle.cli.stories."""

from __future__ import annotations

import subprocess
import sys
from datetime import date
from typing import TYPE_CHECKING

import pytest

from mantle.core.issues import IssueNote
from mantle.core.state import ProjectState, Status
from mantle.core.stories import StoryNote
from mantle.core.vault import read_note, write_note

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
    """Create a minimal .mantle/ with state.md, issues, and stories dirs."""
    (tmp_path / ".mantle").mkdir()
    (tmp_path / ".mantle" / "issues").mkdir()
    (tmp_path / ".mantle" / "stories").mkdir()
    state = ProjectState(
        project="test-project",
        status=Status.PLANNING,
        created=date(2025, 1, 1),
        created_by=MOCK_EMAIL,
        updated=date(2025, 1, 1),
        updated_by=MOCK_EMAIL,
    )
    body = (
        "## Summary\n\n"
        "Test project\n\n"
        "## Current Focus\n\n"
        "Planning stories.\n\n"
        "## Blockers\n\n"
        "_Anything preventing progress?_\n"
    )
    write_note(tmp_path / ".mantle" / "state.md", state, body)
    issue = IssueNote(title="Test issue", slice=("core", "tests"))
    write_note(
        tmp_path / ".mantle" / "issues" / "issue-01.md",
        issue,
        "## What to build\n\nBuild it.\n",
    )
    return tmp_path


def _write_story(
    project_dir: Path,
    *,
    issue: int = 1,
    story: int = 1,
    title: str = "Core module",
    status: str = "planned",
) -> None:
    note = StoryNote(
        issue=issue,
        title=title,
        status=status,
        tags=("type/story", f"status/{status}"),
    )
    write_note(
        project_dir
        / ".mantle"
        / "stories"
        / f"issue-{issue:02d}-story-{story:02d}.md",
        note,
        "## Implementation\n\nBuild it.\n",
    )


# ── run_save_story ─────────────────────────────────────────────


class TestRunSaveStory:
    def test_creates_story_file(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.stories import run_save_story

        run_save_story(
            issue=1,
            title="Core module",
            content="## Implementation\n\nBuild it.\n",
            project_dir=project,
        )

        assert (
            project / ".mantle" / "stories" / "issue-01-story-01.md"
        ).exists()

    def test_prints_confirmation(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.stories import run_save_story

        run_save_story(
            issue=1,
            title="Core module",
            content="## Implementation\n\nBuild it.\n",
            project_dir=project,
        )
        captured = capsys.readouterr()

        assert "issue-01-story-01.md" in captured.out
        assert "Core module" in captured.out
        assert "Stories for issue 1: 1" in captured.out

    def test_defaults_to_cwd(
        self,
        project: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.chdir(project)

        from mantle.cli.stories import run_save_story

        run_save_story(
            issue=1,
            title="Core module",
            content="Build it.\n",
        )
        captured = capsys.readouterr()

        assert "issue-01-story-01.md" in captured.out

    def test_handles_story_exists_error(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.stories import run_save_story

        run_save_story(
            issue=1,
            title="First",
            content="Build it.\n",
            project_dir=project,
        )

        with pytest.raises(SystemExit, match="1"):
            run_save_story(
                issue=1,
                title="Second",
                content="Build it again.\n",
                story=1,
                project_dir=project,
            )

        captured = capsys.readouterr()
        assert "already exists" in captured.out


# ── CLI wiring ─────────────────────────────────────────────────


# ── run_update_story_status ────────────────────────────────────


class TestRunUpdateStoryStatus:
    def test_updates_status(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _write_story(project)

        from mantle.cli.stories import run_update_story_status

        run_update_story_status(
            issue=1,
            story=1,
            status="in-progress",
            project_dir=project,
        )

        path = project / ".mantle" / "stories" / "issue-01-story-01.md"
        note = read_note(path, StoryNote)
        assert note.frontmatter.status == "in-progress"

    def test_prints_confirmation(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _write_story(project)

        from mantle.cli.stories import run_update_story_status

        run_update_story_status(
            issue=1,
            story=1,
            status="completed",
            project_dir=project,
        )
        captured = capsys.readouterr()

        assert "Updated story 1" in captured.out
        assert "completed" in captured.out

    def test_defaults_to_cwd(
        self,
        project: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _write_story(project)
        monkeypatch.chdir(project)

        from mantle.cli.stories import run_update_story_status

        run_update_story_status(
            issue=1,
            story=1,
            status="in-progress",
        )

        path = project / ".mantle" / "stories" / "issue-01-story-01.md"
        note = read_note(path, StoryNote)
        assert note.frontmatter.status == "in-progress"

    def test_handles_not_found(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.stories import run_update_story_status

        with pytest.raises(SystemExit, match="1"):
            run_update_story_status(
                issue=1,
                story=99,
                status="in-progress",
                project_dir=project,
            )

        captured = capsys.readouterr()
        assert "not found" in captured.out


# ── CLI wiring ─────────────────────────────────────────────────


class TestCLIWiring:
    def test_save_story_help(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "mantle.cli.main",
                "save-story",
                "--help",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert "issue" in result.stdout.lower()
        assert "title" in result.stdout.lower()

    def test_update_story_status_help(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "mantle.cli.main",
                "update-story-status",
                "--help",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert "issue" in result.stdout.lower()
        assert "story" in result.stdout.lower()
        assert "status" in result.stdout.lower()
