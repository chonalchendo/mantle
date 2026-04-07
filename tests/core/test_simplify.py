"""Tests for mantle.core.simplify."""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

from mantle.core import simplify

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


# ── collect_issue_files ──────────────────────────────────────────


class TestCollectIssueFiles:
    def test_finds_matching_commits(self, tmp_path: Path) -> None:
        """Files from commits matching issue pattern are returned."""
        project = _init_git_repo(tmp_path)
        _write_issue_file(project, 1)

        # Initial commit so we have a parent
        _commit_file(project, "initial.txt", "chore: initial")

        # Issue-1 commits
        _commit_file(project, "foo.py", "feat(issue-1): add foo")
        _commit_file(project, "bar.py", "feat(issue-1): add bar")

        files = simplify.collect_issue_files(project, 1)

        assert "foo.py" in files
        assert "bar.py" in files

    def test_no_commits_returns_empty(self, tmp_path: Path) -> None:
        """Returns empty tuple for issue with no commits."""
        project = _init_git_repo(tmp_path)
        _write_issue_file(project, 1)

        # Need at least one commit for git log to work
        _commit_file(project, "initial.txt", "chore: initial")

        result = simplify.collect_issue_files(project, 1)

        assert result == ()

    def test_excludes_partial_number_match(self, tmp_path: Path) -> None:
        """Collecting issue-3 does not include commits for issue-30."""
        project = _init_git_repo(tmp_path)
        _write_issue_file(project, 3)

        _commit_file(project, "initial.txt", "chore: initial")
        _commit_file(project, "issue3.py", "feat(issue-3): add issue-3 file")
        _commit_file(project, "issue30.py", "feat(issue-30): add issue-30 file")

        files = simplify.collect_issue_files(project, 3)

        assert "issue3.py" in files
        assert "issue30.py" not in files

    def test_finds_zero_padded_commits(self, tmp_path: Path) -> None:
        """Commits with zero-padded scope like (issue-01) are found."""
        project = _init_git_repo(tmp_path)
        _write_issue_file(project, 1)

        _commit_file(project, "initial.txt", "chore: initial")
        _commit_file(project, "padded.py", "feat(issue-01): add padded file")

        files = simplify.collect_issue_files(project, 1)

        assert "padded.py" in files

    def test_excludes_other_issues(self, tmp_path: Path) -> None:
        """Commits for issue-2 not included when collecting issue-1."""
        project = _init_git_repo(tmp_path)
        _write_issue_file(project, 1)

        _commit_file(project, "initial.txt", "chore: initial")
        _commit_file(project, "foo.py", "feat(issue-1): add foo")
        _commit_file(project, "other.py", "feat(issue-2): add other")

        files = simplify.collect_issue_files(project, 1)

        assert "foo.py" in files
        assert "other.py" not in files


# ── collect_changed_files ────────────────────────────────────────


class TestCollectChangedFiles:
    def test_includes_staged_and_unstaged(self, tmp_path: Path) -> None:
        """Both staged and unstaged changes are returned."""
        project = _init_git_repo(tmp_path)

        # Initial commit
        _commit_file(project, "existing.txt", "chore: initial")

        # Stage a new file
        (project / "staged.txt").write_text("staged", encoding="utf-8")
        subprocess.run(
            ["git", "add", "staged.txt"],
            cwd=project,
            capture_output=True,
            check=True,
        )

        # Modify existing file (unstaged)
        (project / "existing.txt").write_text("modified", encoding="utf-8")

        files = simplify.collect_changed_files(project)

        assert "staged.txt" in files
        assert "existing.txt" in files

    def test_includes_untracked(self, tmp_path: Path) -> None:
        """Untracked files are included in results."""
        project = _init_git_repo(tmp_path)
        _commit_file(project, "initial.txt", "chore: initial")

        (project / "untracked.txt").write_text("new", encoding="utf-8")

        files = simplify.collect_changed_files(project)

        assert "untracked.txt" in files

    def test_empty_when_clean(self, tmp_path: Path) -> None:
        """Clean working tree returns empty tuple."""
        project = _init_git_repo(tmp_path)
        _commit_file(project, "initial.txt", "chore: initial")

        files = simplify.collect_changed_files(project)

        assert files == ()


# ── LLM_BLOAT_CHECKLIST ─────────────────────────────────────────


class TestBloatChecklist:
    def test_contains_all_patterns(self) -> None:
        """Checklist contains all 8 bloat pattern names."""
        patterns = [
            "Unnecessary abstractions",
            "Defensive over-engineering",
            "Code duplication",
            "Unnecessary conditionals",
            "Dead code",
            "Comment noise",
            "Slop scaffolding",
            "Over-parameterisation",
        ]
        for pattern in patterns:
            assert pattern in simplify.LLM_BLOAT_CHECKLIST
