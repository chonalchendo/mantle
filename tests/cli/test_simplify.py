"""Tests for mantle.cli.simplify."""

from __future__ import annotations

import subprocess
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


# ── Helpers ──────────────────────────────────────────────────────


def _init_git_repo(tmp_path: Path) -> Path:
    """Create a git repo with .mantle/issues/ directory."""
    subprocess.run(
        ["git", "init"],
        cwd=tmp_path,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=tmp_path,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=tmp_path,
        capture_output=True,
        check=True,
    )

    mantle = tmp_path / ".mantle"
    mantle.mkdir()
    (mantle / "issues").mkdir()
    return tmp_path


def _write_issue_file(project_root: Path, issue: int) -> None:
    """Write a minimal issue file for testing."""
    path = project_root / ".mantle" / "issues" / f"issue-{issue:02d}-test-issue.md"
    path.write_text(
        f"---\ntitle: Issue {issue}\nstatus: implemented\n"
        f"slice:\n- core\ntags:\n- type/issue\n"
        f"- status/implemented\n---\n\n"
        f"## Acceptance Criteria\n\n- Done\n",
        encoding="utf-8",
    )


def _commit_file(
    project_root: Path,
    filename: str,
    message: str,
) -> None:
    """Create a file and commit it."""
    (project_root / filename).write_text(f"# {filename}\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", filename],
        cwd=project_root,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "commit", "-m", message],
        cwd=project_root,
        capture_output=True,
        check=True,
    )


# ── collect-issue-files ──────────────────────────────────────────


class TestCollectIssueFilesCLI:
    def test_prints_files(self, tmp_path: Path) -> None:
        """Happy path: prints files changed by issue commits."""
        project = _init_git_repo(tmp_path)
        _write_issue_file(project, 1)
        _commit_file(project, "initial.txt", "chore: initial")
        _commit_file(project, "foo.py", "feat(issue-1): add foo")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "mantle.cli.main",
                "collect-issue-files",
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
        assert "foo.py" in result.stdout

    def test_no_commits_prints_message(self, tmp_path: Path) -> None:
        """Prints message and exits 0 when no commits match."""
        project = _init_git_repo(tmp_path)
        _write_issue_file(project, 1)
        _commit_file(project, "initial.txt", "chore: initial")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "mantle.cli.main",
                "collect-issue-files",
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
        assert "No commits found" in result.stdout


# ── collect-changed-files ────────────────────────────────────────


class TestCollectChangedFilesCLI:
    def test_prints_files(self, tmp_path: Path) -> None:
        """Happy path: prints changed files."""
        project = _init_git_repo(tmp_path)
        _commit_file(project, "initial.txt", "chore: initial")

        (project / "new_file.txt").write_text("hello", encoding="utf-8")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "mantle.cli.main",
                "collect-changed-files",
                "--path",
                str(project),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0
        assert "new_file.txt" in result.stdout
