"""Tests for mantle.cli.learning."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from mantle.cli import learning as cli_learning
from mantle.core import issues as core_issues
from mantle.core import vault

if TYPE_CHECKING:
    from pathlib import Path


MOCK_EMAIL = "test@example.com"
CONTENT = (
    "## What went well\n\nTests passed on first try.\n\n"
    "## Harder than expected\n\nAPI integration was tricky.\n"
)


def _mock_git_identity() -> str:
    return MOCK_EMAIL


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """Create a minimal .mantle/ with the standard subdirs."""
    mantle = tmp_path / ".mantle"
    mantle.mkdir()
    for subdir in ("issues", "stories", "shaped", "learnings"):
        (mantle / subdir).mkdir()
    _write_state(tmp_path)
    return tmp_path


def _write_state(project_dir: Path) -> None:
    """Write a minimal state.md so _update_state_body can run."""
    from datetime import date

    from mantle.core.state import ProjectState, Status

    st = ProjectState(
        project="test-project",
        status=Status.IMPLEMENTING,
        confidence="7/10",
        created=date(2025, 1, 1),
        created_by=MOCK_EMAIL,
        updated=date(2025, 1, 1),
        updated_by=MOCK_EMAIL,
    )
    body = (
        "## Summary\n\nTest project\n\n"
        "## Current Focus\n\nImplementing.\n\n"
        "## Blockers\n\nNone.\n"
    )
    vault.write_note(project_dir / ".mantle" / "state.md", st, body)


def _write_issue(
    project_dir: Path,
    issue: int,
    *,
    status: str = "implementing",
) -> Path:
    """Write a minimal issue file and return its path."""
    note = core_issues.IssueNote(
        title=f"Test issue {issue}",
        status=status,
        slice=("core",),
        tags=(
            "type/issue",
            f"status/{status}",
        ),
    )
    slug = f"test-issue-{issue}"
    path = project_dir / ".mantle" / "issues" / f"issue-{issue:02d}-{slug}.md"
    vault.write_note(path, note, "## Acceptance Criteria\n\n- It works\n")
    return path


def _write_shaped(project_dir: Path, issue: int) -> Path:
    """Write a minimal shaped doc and return its path."""
    path = (
        project_dir
        / ".mantle"
        / "shaped"
        / f"issue-{issue:02d}-test-issue-{issue}-shaped.md"
    )
    path.write_text("---\ntitle: Shaped\n---\nApproach\n")
    return path


def _write_story(project_dir: Path, issue: int, story: int) -> Path:
    """Write a minimal story file and return its path."""
    path = (
        project_dir
        / ".mantle"
        / "stories"
        / f"issue-{issue:02d}-test-issue-{issue}-story-{story:02d}.md"
    )
    path.write_text(
        f"---\nissue: {issue}\ntitle: Story {story}\n"
        f"status: completed\ntags: [type/story]\n---\nBody\n"
    )
    return path


def _call_save_learning(project_dir: Path, issue: int = 1) -> None:
    """Invoke run_save_learning with sensible defaults."""
    cli_learning.run_save_learning(
        issue=issue,
        title="Test learning",
        confidence_delta="+1",
        content=CONTENT,
        project_dir=project_dir,
    )


class TestSaveLearningNoArchive:
    """Regression tests: save-learning must not move files."""

    @patch(
        "mantle.core.learning.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_save_learning_does_not_archive_issue_file(
        self, _mock: object, project: Path
    ) -> None:
        issue_path = _write_issue(project, 1)

        _call_save_learning(project)

        assert issue_path.exists()
        archive_issue = (
            project / ".mantle" / "archive" / "issues" / issue_path.name
        )
        assert not archive_issue.exists()

    @patch(
        "mantle.core.learning.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_save_learning_does_not_archive_shaped_doc(
        self, _mock: object, project: Path
    ) -> None:
        _write_issue(project, 1)
        shaped_path = _write_shaped(project, 1)

        _call_save_learning(project)

        assert shaped_path.exists()
        archive_shaped = (
            project / ".mantle" / "archive" / "shaped" / shaped_path.name
        )
        assert not archive_shaped.exists()

    @patch(
        "mantle.core.learning.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_save_learning_does_not_archive_stories(
        self, _mock: object, project: Path
    ) -> None:
        _write_issue(project, 1)
        story_one = _write_story(project, 1, 1)
        story_two = _write_story(project, 1, 2)

        _call_save_learning(project)

        assert story_one.exists()
        assert story_two.exists()
        archive_stories = project / ".mantle" / "archive" / "stories"
        assert not (archive_stories / story_one.name).exists()
        assert not (archive_stories / story_two.name).exists()

    @patch(
        "mantle.core.learning.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_save_learning_mid_pipeline_regression(
        self, _mock: object, project: Path
    ) -> None:
        """Full mid-pipeline scene — nothing should be moved."""
        issue_path = _write_issue(project, 1)
        shaped_path = _write_shaped(project, 1)
        story_one = _write_story(project, 1, 1)
        story_two = _write_story(project, 1, 2)

        _call_save_learning(project)

        learning_path = (
            project / ".mantle" / "learnings" / "issue-01-test-learning.md"
        )
        assert learning_path.exists()

        assert issue_path.exists()
        assert shaped_path.exists()
        assert story_one.exists()
        assert story_two.exists()

        archive_dir = project / ".mantle" / "archive"
        assert not archive_dir.exists() or not any(archive_dir.rglob("*.md"))

    @patch(
        "mantle.core.learning.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_save_learning_writes_learning_file(
        self, _mock: object, project: Path
    ) -> None:
        _write_issue(project, 1)

        _call_save_learning(project)

        learning_path = (
            project / ".mantle" / "learnings" / "issue-01-test-learning.md"
        )
        assert learning_path.exists()
        text = learning_path.read_text()
        assert "What went well" in text
        assert "Tests passed on first try" in text
