"""Tests for mantle.cli.review."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from mantle.cli import review as cli_review
from mantle.core import issues as core_issues
from mantle.core import vault

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """Create a minimal .mantle/ with issues dir."""
    mantle = tmp_path / ".mantle"
    mantle.mkdir()
    (mantle / "issues").mkdir()
    return tmp_path


def _write_issue(
    project: Path,
    issue: int,
    *,
    status: str = "verified",
) -> None:
    """Write a minimal issue file with a given status."""
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
    path = project / ".mantle" / "issues" / f"issue-{issue:02d}-{slug}.md"
    vault.write_note(path, note, "## Acceptance Criteria\n\n- It works\n")


class TestTransitionIssueApprovedCLI:
    def test_transition_to_approved_success(
        self,
        project: Path,
    ) -> None:
        _write_issue(project, 1, status="verified")

        cli_review.run_transition_to_approved(issue=1, project_dir=project)

        archived_path = (
            project
            / ".mantle"
            / "archive"
            / "issues"
            / "issue-01-test-issue-1.md"
        )
        note, _ = core_issues.load_issue(archived_path)
        assert note.status == "approved"

    def test_transition_to_approved_invalid_status(
        self,
        project: Path,
    ) -> None:
        _write_issue(project, 1, status="planned")

        with pytest.raises(SystemExit):
            cli_review.run_transition_to_approved(issue=1, project_dir=project)

    def test_transition_to_approved_archives_issue_artifacts(
        self,
        project: Path,
    ) -> None:
        _write_issue(project, 1, status="verified")
        mantle = project / ".mantle"
        (mantle / "shaped").mkdir()
        (mantle / "stories").mkdir()
        shaped = mantle / "shaped" / "issue-01-test-issue-1-shaped.md"
        shaped.write_text("---\ntitle: Shaped\n---\nApproach\n")
        story_one = mantle / "stories" / "issue-01-test-issue-1-story-01.md"
        story_one.write_text(
            "---\nissue: 1\ntitle: Story 1\nstatus: completed\n"
            "tags: [type/story]\n---\nBody\n"
        )
        story_two = mantle / "stories" / "issue-01-test-issue-1-story-02.md"
        story_two.write_text(
            "---\nissue: 1\ntitle: Story 2\nstatus: completed\n"
            "tags: [type/story]\n---\nBody\n"
        )

        cli_review.run_transition_to_approved(issue=1, project_dir=project)

        archive_dir = mantle / "archive"
        assert (archive_dir / "issues" / "issue-01-test-issue-1.md").exists()
        assert (
            archive_dir / "shaped" / "issue-01-test-issue-1-shaped.md"
        ).exists()
        assert (
            archive_dir / "stories" / "issue-01-test-issue-1-story-01.md"
        ).exists()
        assert (
            archive_dir / "stories" / "issue-01-test-issue-1-story-02.md"
        ).exists()

        assert not (mantle / "issues" / "issue-01-test-issue-1.md").exists()
        assert not shaped.exists()
        assert not story_one.exists()
        assert not story_two.exists()

    def test_transition_to_approved_archives_learning_if_present(
        self,
        project: Path,
    ) -> None:
        _write_issue(project, 1, status="verified")
        mantle = project / ".mantle"
        (mantle / "learnings").mkdir()
        learning_path = mantle / "learnings" / "issue-01-test-issue-1.md"
        learning_path.write_text(
            "---\nissue: 1\ntitle: Test\nauthor: a@b.com\n"
            "date: 2026-01-01\nconfidence_delta: '+1'\n"
            "tags: [type/learning]\n---\nLearning\n"
        )

        cli_review.run_transition_to_approved(issue=1, project_dir=project)

        archived = mantle / "archive" / "learnings" / "issue-01-test-issue-1.md"
        assert archived.exists()
        assert not learning_path.exists()

    def test_transition_to_approved_archive_noop_when_nothing_to_archive(
        self,
        project: Path,
    ) -> None:
        _write_issue(project, 1, status="verified")

        cli_review.run_transition_to_approved(issue=1, project_dir=project)

        archive_dir = project / ".mantle" / "archive"
        assert (archive_dir / "issues" / "issue-01-test-issue-1.md").exists()


class TestTransitionIssueImplementingCLI:
    def test_transition_to_implementing_success(
        self,
        project: Path,
    ) -> None:
        _write_issue(project, 1, status="verified")

        cli_review.run_transition_to_implementing(issue=1, project_dir=project)

        issue_path = project / ".mantle" / "issues" / "issue-01-test-issue-1.md"
        note, _ = core_issues.load_issue(issue_path)
        assert note.status == "implementing"

    def test_transition_to_implementing_invalid_status(
        self,
        project: Path,
    ) -> None:
        _write_issue(project, 1, status="approved")

        with pytest.raises(SystemExit):
            cli_review.run_transition_to_implementing(
                issue=1, project_dir=project
            )


class TestTransitionIssueImplementedCLI:
    def test_transition_to_implemented_success(
        self,
        project: Path,
    ) -> None:
        """Calls core function, prints confirmation."""
        _write_issue(project, 1, status="implementing")

        cli_review.run_transition_to_implemented(issue=1, project_dir=project)

        issue_path = project / ".mantle" / "issues" / "issue-01-test-issue-1.md"
        note, _ = core_issues.load_issue(issue_path)
        assert note.status == "implemented"

    def test_transition_to_implemented_invalid_status(
        self,
        project: Path,
    ) -> None:
        """Prints error and exits."""
        _write_issue(project, 1, status="planned")

        with pytest.raises(SystemExit):
            cli_review.run_transition_to_implemented(
                issue=1, project_dir=project
            )
