"""Tests for mantle.cli.review."""

from __future__ import annotations

import subprocess
import sys
from typing import TYPE_CHECKING

import pytest

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
    path = project / ".mantle" / "issues" / f"issue-{issue:02d}.md"
    vault.write_note(path, note, "## Acceptance Criteria\n\n- It works\n")


class TestTransitionIssueApprovedCLI:
    def test_transition_to_approved_success(
        self,
        project: Path,
    ) -> None:
        _write_issue(project, 1, status="verified")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "mantle.cli.main",
                "transition-issue-approved",
                "--issue",
                "1",
                "--path",
                str(project),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0
        assert "approved" in result.stdout.lower()

        # Verify the issue file was updated.
        issue_path = project / ".mantle" / "issues" / "issue-01.md"
        note, _ = core_issues.load_issue(issue_path)
        assert note.status == "approved"

    def test_transition_to_approved_invalid_status(
        self,
        project: Path,
    ) -> None:
        _write_issue(project, 1, status="planned")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "mantle.cli.main",
                "transition-issue-approved",
                "--issue",
                "1",
                "--path",
                str(project),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode != 0
        assert "Cannot transition" in result.stdout


class TestTransitionIssueImplementingCLI:
    def test_transition_to_implementing_success(
        self,
        project: Path,
    ) -> None:
        _write_issue(project, 1, status="verified")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "mantle.cli.main",
                "transition-issue-implementing",
                "--issue",
                "1",
                "--path",
                str(project),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0
        assert "implementing" in result.stdout.lower()

        # Verify the issue file was updated.
        issue_path = project / ".mantle" / "issues" / "issue-01.md"
        note, _ = core_issues.load_issue(issue_path)
        assert note.status == "implementing"

    def test_transition_to_implementing_invalid_status(
        self,
        project: Path,
    ) -> None:
        _write_issue(project, 1, status="implemented")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "mantle.cli.main",
                "transition-issue-implementing",
                "--issue",
                "1",
                "--path",
                str(project),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode != 0
        assert "Cannot transition" in result.stdout
