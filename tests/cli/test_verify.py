"""Tests for mantle.cli.verify."""

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
    """Create a minimal .mantle/ with config.md and issues dir."""
    mantle = tmp_path / ".mantle"
    mantle.mkdir()
    (mantle / "issues").mkdir()

    # Minimal config.md with empty frontmatter.
    (mantle / "config.md").write_text(
        "---\n---\n\n# Configuration\n",
        encoding="utf-8",
    )
    return tmp_path


def _write_issue(
    project: Path,
    issue: int,
    *,
    status: str = "implemented",
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


class TestSaveVerificationStrategyCLI:
    def test_saves_strategy_to_config(
        self,
        project: Path,
    ) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "mantle.cli.main",
                "save-verification-strategy",
                "--strategy",
                "run pytest",
                "--path",
                str(project),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0
        assert "Verification strategy saved" in result.stdout

        config_text = (project / ".mantle" / "config.md").read_text(
            encoding="utf-8"
        )
        assert "run pytest" in config_text


class TestTransitionIssueVerifiedCLI:
    def test_transitions_implemented_issue(
        self,
        project: Path,
    ) -> None:
        _write_issue(project, 1, status="implemented")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "mantle.cli.main",
                "transition-issue-verified",
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
        assert "verified" in result.stdout.lower()

        # Verify the issue file was updated.
        issue_path = (
            project / ".mantle" / "issues" / "issue-01-test-issue-1.md"
        )
        note, _ = core_issues.load_issue(issue_path)
        assert note.status == "verified"

    def test_rejects_invalid_transition(
        self,
        project: Path,
    ) -> None:
        _write_issue(project, 1, status="planned")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "mantle.cli.main",
                "transition-issue-verified",
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
