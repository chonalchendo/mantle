"""Tests for mantle.core.simplify."""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

import yaml

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
    path = (
        project_root / ".mantle" / "issues" / f"issue-{issue:02d}-test-issue.md"
    )
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


def _write_config_md(
    project_root: Path,
    diff_paths: dict[str, list[str]],
) -> None:
    """Write a minimal .mantle/config.md with a diff_paths frontmatter block."""
    config_path = project_root / ".mantle" / "config.md"
    yaml_str = yaml.dump(
        {"diff_paths": diff_paths},
        default_flow_style=False,
        sort_keys=False,
    )
    config_path.write_text(f"---\n{yaml_str}---\n\n", encoding="utf-8")


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


# ── collect_issue_diff_stats ─────────────────────────────────────


def _commit_content(
    project_root: Path,
    filename: str,
    content: str,
    message: str,
) -> None:
    """Write file content and commit it, creating parent directories."""
    path = project_root / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
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


class TestCollectIssueDiffStats:
    def test_returns_zeros_when_no_commits(self, tmp_path: Path) -> None:
        """Returns DiffStats(0, 0, 0, 0) when no matching commits."""
        project = _init_git_repo(tmp_path)
        _write_issue_file(project, 1)
        _commit_file(project, "initial.txt", "chore: initial")

        stats = simplify.collect_issue_diff_stats(project, 1)

        assert stats == simplify.DiffStats(0, 0, 0, 0)

    def test_single_commit(self, tmp_path: Path) -> None:
        """Single matching commit reports correct file and line counts."""
        project = _init_git_repo(tmp_path)
        _write_issue_file(project, 7)
        _commit_file(project, "initial.txt", "chore: initial")

        content = "".join(f"line {i}\n" for i in range(10))
        _commit_content(
            project, "src/foo.py", content, "feat(issue-7): add foo"
        )

        stats = simplify.collect_issue_diff_stats(project, 7)

        assert stats.files == 1
        assert stats.lines_added == 10
        assert stats.lines_removed == 0
        assert stats.lines_changed == 10

    def test_multi_commit_aggregation(self, tmp_path: Path) -> None:
        """Stats aggregate across multiple matching commits."""
        project = _init_git_repo(tmp_path)
        _write_issue_file(project, 7)
        _commit_file(project, "initial.txt", "chore: initial")

        content_a = "".join(f"a{i}\n" for i in range(5))
        _commit_content(project, "src/a.py", content_a, "feat(issue-7): add a")

        content_b = "".join(f"b{i}\n" for i in range(8))
        _commit_content(project, "src/b.py", content_b, "feat(issue-7): add b")

        stats = simplify.collect_issue_diff_stats(project, 7)

        assert stats.files == 2
        assert stats.lines_added == 13
        assert stats.lines_removed == 0
        assert stats.lines_changed == 13

    def test_only_deletions(self, tmp_path: Path) -> None:
        """Pure deletion commits report lines_removed only."""
        project = _init_git_repo(tmp_path)
        _write_issue_file(project, 7)

        content = "".join(f"line {i}\n" for i in range(6))
        _commit_content(project, "src/foo.py", content, "chore: initial foo")
        _commit_content(project, "src/foo.py", "", "feat(issue-7): empty foo")

        stats = simplify.collect_issue_diff_stats(project, 7)

        assert stats.files == 1
        assert stats.lines_added == 0
        assert stats.lines_removed == 6
        assert stats.lines_changed == 6

    def test_unknown_issue_raises(self, tmp_path: Path) -> None:
        """Unknown issue number raises FileNotFoundError."""
        project = _init_git_repo(tmp_path)
        _commit_file(project, "initial.txt", "chore: initial")

        try:
            simplify.collect_issue_diff_stats(project, 999)
        except FileNotFoundError:
            return
        msg = "Expected FileNotFoundError"
        raise AssertionError(msg)

    def test_handles_padded_single_digit(self, tmp_path: Path) -> None:
        """For issue N<10, finds commits written as (issue-0N)."""
        project = _init_git_repo(tmp_path)
        _write_issue_file(project, 1)
        _commit_file(project, "initial.txt", "chore: initial")

        content = "".join(f"p{i}\n" for i in range(4))
        _commit_content(
            project,
            "src/padded.py",
            content,
            "feat(issue-01): add padded",
        )

        stats = simplify.collect_issue_diff_stats(project, 1)

        assert stats.files == 1
        assert stats.lines_added == 4
        assert stats.lines_changed == 4

    def test_excludes_claude_paths(self, tmp_path: Path) -> None:
        """Commits touching only claude/ paths report DiffStats(0,0,0,0)."""
        project = _init_git_repo(tmp_path)
        _write_issue_file(project, 7)
        _commit_file(project, "initial.txt", "chore: initial")

        _commit_content(
            project,
            "claude/commands/mantle/foo.md",
            "# foo\n",
            "feat(issue-7): add foo doc",
        )

        stats = simplify.collect_issue_diff_stats(project, 7)

        assert stats == simplify.DiffStats(0, 0, 0, 0)

    def test_excludes_mantle_paths(self, tmp_path: Path) -> None:
        """Commits touching only .mantle/ paths report DiffStats(0,0,0,0)."""
        project = _init_git_repo(tmp_path)
        _write_issue_file(project, 7)
        _commit_file(project, "initial.txt", "chore: initial")

        _commit_content(
            project,
            ".mantle/learnings/x.md",
            "# learning\n",
            "feat(issue-7): add learning",
        )

        stats = simplify.collect_issue_diff_stats(project, 7)

        assert stats == simplify.DiffStats(0, 0, 0, 0)

    def test_counts_only_src_and_tests_when_mixed(self, tmp_path: Path) -> None:
        """Only src/ lines counted when diff also touches claude/ paths."""
        project = _init_git_repo(tmp_path)
        _write_issue_file(project, 7)
        _commit_file(project, "initial.txt", "chore: initial")

        src_content = "".join(f"line {i}\n" for i in range(10))
        _commit_content(
            project,
            "src/foo.py",
            src_content,
            "feat(issue-7): add src file",
        )

        _commit_content(
            project,
            "claude/bar.md",
            "".join(f"prose {i}\n" for i in range(20)),
            "feat(issue-7): add claude doc",
        )

        stats = simplify.collect_issue_diff_stats(project, 7)

        assert stats.files == 1
        assert stats.lines_added == 10
        assert stats.lines_changed == 10

    def test_counts_tests_directory(self, tmp_path: Path) -> None:
        """Commits touching tests/ paths are counted."""
        project = _init_git_repo(tmp_path)
        _write_issue_file(project, 7)
        _commit_file(project, "initial.txt", "chore: initial")

        content = "".join(f"t{i}\n" for i in range(5))
        _commit_content(
            project,
            "tests/test_foo.py",
            content,
            "feat(issue-7): add test",
        )

        stats = simplify.collect_issue_diff_stats(project, 7)

        assert stats.files == 1
        assert stats.lines_changed == 5

    def test_aggregate_sums_only_primary_categories(
        self, tmp_path: Path
    ) -> None:
        """Aggregate wrapper excludes non-primary categories (docs)."""
        project = _init_git_repo(tmp_path)
        _write_issue_file(project, 7)
        _write_config_md(
            project,
            {
                "source": ["src/"],
                "test": ["tests/"],
                "docs": ["docs/"],
            },
        )
        _commit_file(project, "initial.txt", "chore: initial")

        src_content = "".join(f"s{i}\n" for i in range(4))
        _commit_content(
            project, "src/a.py", src_content, "feat(issue-7): add src"
        )
        test_content = "".join(f"t{i}\n" for i in range(2))
        _commit_content(
            project, "tests/t.py", test_content, "feat(issue-7): add test"
        )
        docs_content = "".join(f"d{i}\n" for i in range(10))
        _commit_content(
            project, "docs/d.md", docs_content, "feat(issue-7): add docs"
        )

        stats = simplify.collect_issue_diff_stats(project, 7)

        assert stats.files == 2
        assert stats.lines_changed == 6


# ── load_diff_paths ──────────────────────────────────────────────


class TestLoadDiffPaths:
    def test_defaults_when_config_missing(self, tmp_path: Path) -> None:
        """No config.md present — returns defaults, is_custom=False."""
        project = _init_git_repo(tmp_path)

        paths, is_custom = simplify.load_diff_paths(project)

        assert paths == simplify.DEFAULT_DIFF_PATHS
        assert is_custom is False

    def test_defaults_when_field_absent(self, tmp_path: Path) -> None:
        """config.md without diff_paths field — returns defaults."""
        project = _init_git_repo(tmp_path)
        config_path = project / ".mantle" / "config.md"
        config_path.write_text("---\n---\n\n", encoding="utf-8")

        paths, is_custom = simplify.load_diff_paths(project)

        assert paths == simplify.DEFAULT_DIFF_PATHS
        assert is_custom is False

    def test_returns_custom_when_field_present(self, tmp_path: Path) -> None:
        """diff_paths field present — returns mapping, is_custom=True."""
        project = _init_git_repo(tmp_path)
        _write_config_md(
            project,
            {
                "source": ["models/"],
                "test": ["tests/"],
                "macros": ["macros/"],
            },
        )

        paths, is_custom = simplify.load_diff_paths(project)

        assert paths == {
            "source": ("models/",),
            "test": ("tests/",),
            "macros": ("macros/",),
        }
        assert is_custom is True


# ── collect_issue_diff_stats_categorised ─────────────────────────


class TestCollectIssueDiffStatsCategorised:
    def test_defaults_no_other_bucket(self, tmp_path: Path) -> None:
        """Defaults mode: returned dict has source+test keys only."""
        project = _init_git_repo(tmp_path)
        _write_issue_file(project, 7)
        _commit_file(project, "initial.txt", "chore: initial")

        content = "".join(f"line {i}\n" for i in range(3))
        _commit_content(
            project, "src/foo.py", content, "feat(issue-7): add foo"
        )

        categories = simplify.collect_issue_diff_stats_categorised(project, 7)

        assert set(categories.keys()) == {"source", "test"}
        assert categories["source"].files == 1

    def test_defaults_drop_unclassified(self, tmp_path: Path) -> None:
        """Defaults mode: unclassified files dropped silently, no other key."""
        project = _init_git_repo(tmp_path)
        _write_issue_file(project, 7)
        _commit_file(project, "initial.txt", "chore: initial")

        src_content = "".join(f"line {i}\n" for i in range(4))
        _commit_content(
            project, "src/foo.py", src_content, "feat(issue-7): add src"
        )
        _commit_content(
            project,
            "claude/bar.md",
            "# bar\n",
            "feat(issue-7): add claude",
        )

        categories = simplify.collect_issue_diff_stats_categorised(project, 7)

        assert categories["source"].files == 1
        assert "other" not in categories

    def test_custom_config_adds_other_bucket(self, tmp_path: Path) -> None:
        """Explicit config — unclassified files go into other bucket."""
        project = _init_git_repo(tmp_path)
        _write_issue_file(project, 7)
        _write_config_md(
            project,
            {"source": ["src/"], "test": ["tests/"]},
        )
        _commit_file(project, "initial.txt", "chore: initial")

        _commit_content(
            project,
            "src/x.py",
            "x = 1\n",
            "feat(issue-7): add src",
        )
        _commit_content(
            project,
            "docs/y.md",
            "# doc\n",
            "feat(issue-7): add doc",
        )

        categories = simplify.collect_issue_diff_stats_categorised(project, 7)

        assert categories["source"].files == 1
        assert categories["other"].files == 1

    def test_dbt_style_fixture(self, tmp_path: Path) -> None:
        """dbt-style layout with models/, tests/, macros/ categories."""
        project = _init_git_repo(tmp_path)
        _write_issue_file(project, 7)
        _write_config_md(
            project,
            {
                "source": ["models/"],
                "test": ["tests/"],
                "macros": ["macros/"],
            },
        )
        _commit_file(project, "initial.txt", "chore: initial")

        models_content = "".join(f"m{i}\n" for i in range(3))
        _commit_content(
            project,
            "models/stg_a.sql",
            models_content,
            "feat(issue-7): add model",
        )
        tests_content = "".join(f"t{i}\n" for i in range(1))
        _commit_content(
            project,
            "tests/generic_b.sql",
            tests_content,
            "feat(issue-7): add test",
        )
        macros_content = "".join(f"x{i}\n" for i in range(5))
        _commit_content(
            project,
            "macros/util.sql",
            macros_content,
            "feat(issue-7): add macro",
        )
        other_content = "".join(f"o{i}\n" for i in range(2))
        _commit_content(
            project,
            ".mantle/x.md",
            other_content,
            "feat(issue-7): add mantle note",
        )

        categories = simplify.collect_issue_diff_stats_categorised(project, 7)

        assert categories["source"].files == 1
        assert categories["source"].lines_changed == 3
        assert categories["test"].files == 1
        assert categories["test"].lines_changed == 1
        assert categories["macros"].files == 1
        assert categories["macros"].lines_changed == 5
        assert categories["other"].files == 1

    def test_first_match_wins(self, tmp_path: Path) -> None:
        """Files matching multiple prefixes bucket into first declared."""
        project = _init_git_repo(tmp_path)
        _write_issue_file(project, 7)
        _write_config_md(
            project,
            {"source": ["src/"], "vendor": ["src/vendor/"]},
        )
        _commit_file(project, "initial.txt", "chore: initial")

        _commit_content(
            project,
            "src/vendor/a.py",
            "a = 1\n",
            "feat(issue-7): add vendored file",
        )

        categories = simplify.collect_issue_diff_stats_categorised(project, 7)

        assert categories["source"].files == 1
        assert categories["vendor"].files == 0

    def test_empty_categories_always_present(self, tmp_path: Path) -> None:
        """No matching commits: every declared category present, zeroed."""
        project = _init_git_repo(tmp_path)
        _write_issue_file(project, 1)
        _commit_file(project, "initial.txt", "chore: initial")

        categories = simplify.collect_issue_diff_stats_categorised(project, 1)

        assert categories["source"] == simplify.DiffStats(0, 0, 0, 0)
        assert categories["test"] == simplify.DiffStats(0, 0, 0, 0)
        assert "other" not in categories


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
