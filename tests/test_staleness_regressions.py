"""Regression tests for cross-command side-effect ordering bugs.

These tests exercise multi-step CLI sequences where one command's side
effects affect another. They catch the recurring pattern from issues 46,
47, and 49 where commands fail because prior commands archived or moved
files unexpectedly.
"""

from __future__ import annotations

import subprocess
import textwrap
from datetime import date
from typing import TYPE_CHECKING

import pytest

from mantle.core import archive, issues, project, skills, stories, vault
from mantle.core.project import _ConfigFrontmatter
from mantle.core.skills import SkillNote
from mantle.core.state import ProjectState, Status

if TYPE_CHECKING:
    from pathlib import Path

MOCK_EMAIL = "test@example.com"


# ── Shared fixture helper ───────────────────────────────────────


def _make_mantle_fixture(
    tmp_path: Path,
    *,
    issue: int = 50,
    issue_title: str = "Test issue",
    issue_status: str = "implementing",
    extra_skills: tuple[tuple[str, tuple[str, ...]], ...] = (),
) -> Path:
    """Scaffold a minimal but realistic .mantle/ in tmp_path.

    Each extra_skills entry is ``(skill_name, tags)``. When provided,
    a personal vault is created at tmp_path/vault with config.md pointing
    to it and ``type/skill`` is added to each skill's tags automatically.

    Args:
        tmp_path: Pytest tmp_path fixture.
        issue: Issue number to scaffold.
        issue_title: Issue title (used in filename slug).
        issue_status: Status to write into the issue frontmatter.
        extra_skills: Skills to create in the personal vault.

    Returns:
        Path to the project root (same as tmp_path).
    """
    mantle_dir = tmp_path / ".mantle"
    for subdir in ("issues", "stories", "shaped", "learnings", "reviews"):
        (mantle_dir / subdir).mkdir(parents=True, exist_ok=True)

    # state.md — allows CLI commands that read project state to resolve.
    state_note = ProjectState(
        project="test-project",
        status=Status.IMPLEMENTING,
        created=date(2026, 1, 1),
        created_by=MOCK_EMAIL,
        updated=date(2026, 1, 1),
        updated_by=MOCK_EMAIL,
        current_issue=issue,
    )
    vault.write_note(
        mantle_dir / "state.md",
        state_note,
        "## Summary\n\nTest project.\n\n"
        "## Current Focus\n\nImplementing.\n\n"
        "## Blockers\n\nNone.\n\n"
        "## Recent Decisions\n\nNone.\n\n"
        "## Next Steps\n\nNone.\n",
    )

    # Issue file.
    issue_note = issues.IssueNote(
        title=issue_title,
        status=issue_status,
        slice=("core",),
        tags=("type/issue", f"status/{issue_status}"),
    )
    slug = issues._slugify_title(issue_title)
    issue_path = mantle_dir / "issues" / f"issue-{issue:02d}-{slug}.md"
    vault.write_note(
        issue_path,
        issue_note,
        "## Acceptance Criteria\n\n- It works\n",
    )

    # Personal vault + skill files, only when requested.
    if extra_skills:
        vault_path = tmp_path / "vault"
        (vault_path / "skills").mkdir(parents=True, exist_ok=True)
        config_fm = _ConfigFrontmatter(personal_vault=str(vault_path))
        vault.write_note(mantle_dir / "config.md", config_fm, "## Config\n")

        for name, tags in extra_skills:
            _write_skill_file(vault_path / "skills", name, tags)

    return tmp_path


def _write_skill_file(
    skills_dir: Path,
    name: str,
    tags: tuple[str, ...],
) -> None:
    """Write a minimal skill file to skills_dir (``type/skill`` auto-added)."""
    slug = skills._slugify(name)
    note = SkillNote(
        name=name,
        description=f"Test skill covering {name}.",
        proficiency="5/10",
        last_used=date(2026, 1, 1),
        author=MOCK_EMAIL,
        created=date(2026, 1, 1),
        updated=date(2026, 1, 1),
        updated_by=MOCK_EMAIL,
        tags=("type/skill", *tags),
    )
    vault.write_note(skills_dir / f"{slug}.md", note, "## Context\n\nTest body.\n")


def _run_mantle(
    *args: str,
    cwd: Path,
) -> subprocess.CompletedProcess[str]:
    """Run ``uv run mantle`` so working-tree source is exercised over PATH."""
    return subprocess.run(
        ["uv", "run", "mantle", *args],
        capture_output=True,
        text=True,
        cwd=cwd,
        check=False,
    )


# ── Test classes ────────────────────────────────────────────────


class TestCompileLifecycle:
    """Compile-modify-recompile regression tests for skill indexes."""

    def test_compile_creates_index_for_new_skill(self, tmp_path: Path) -> None:
        _make_mantle_fixture(
            tmp_path,
            extra_skills=(("Finance data ingest", ("topic/finance",)),),
        )
        skills.generate_index_notes(tmp_path)

        index = tmp_path / "vault" / "indexes" / "topic-finance.md"
        assert index.exists()
        assert "[[finance-data-ingest]]" in index.read_text(encoding="utf-8")

    def test_compile_updates_index_when_skill_modified(
        self, tmp_path: Path
    ) -> None:
        _make_mantle_fixture(
            tmp_path,
            extra_skills=(("Finance data ingest", ("topic/finance",)),),
        )
        skills.generate_index_notes(tmp_path)

        # Modify the skill — add a second tag.
        vault_skills = tmp_path / "vault" / "skills"
        _write_skill_file(
            vault_skills,
            "Finance data ingest",
            ("topic/finance", "domain/database"),
        )
        skills.generate_index_notes(tmp_path)

        indexes_dir = tmp_path / "vault" / "indexes"
        assert (indexes_dir / "topic-finance.md").exists()
        assert (indexes_dir / "domain-database.md").exists()
        domain_content = (indexes_dir / "domain-database.md").read_text(
            encoding="utf-8"
        )
        assert "[[finance-data-ingest]]" in domain_content

    def test_compile_deletes_orphaned_index_when_skill_removed(
        self, tmp_path: Path
    ) -> None:
        _make_mantle_fixture(
            tmp_path,
            extra_skills=(
                ("Finance data ingest", ("topic/scraping",)),
                ("Keeper skill", ("domain/web",)),
            ),
        )
        skills.generate_index_notes(tmp_path)

        indexes_dir = tmp_path / "vault" / "indexes"
        orphan = indexes_dir / "topic-scraping.md"
        assert orphan.exists()

        # Remove the only skill tagged topic/scraping.
        (tmp_path / "vault" / "skills" / "finance-data-ingest.md").unlink()
        skills.generate_index_notes(tmp_path)

        assert not orphan.exists()
        # The other index is preserved.
        assert (indexes_dir / "domain-web.md").exists()


class TestCommandOrdering:
    """save-review-result vs transition-issue-approved ordering."""

    def test_save_review_result_succeeds_before_transition_approved(
        self, tmp_path: Path
    ) -> None:
        _make_mantle_fixture(tmp_path, issue=50, issue_status="verified")

        result = _run_mantle(
            "save-review-result",
            "--issue",
            "50",
            "--feedback",
            "It works|approved|",
            cwd=tmp_path,
        )
        assert result.returncode == 0, (
            f"stdout={result.stdout!r} stderr={result.stderr!r}"
        )
        review_file = tmp_path / ".mantle" / "reviews" / "issue-50-review.md"
        assert review_file.exists()

    def test_save_review_result_after_archival_fails_gracefully(
        self, tmp_path: Path
    ) -> None:
        _make_mantle_fixture(tmp_path, issue=50, issue_status="verified")

        approve = _run_mantle(
            "transition-issue-approved",
            "--issue",
            "50",
            cwd=tmp_path,
        )
        assert approve.returncode == 0, (
            f"transition failed: stdout={approve.stdout!r}"
            f" stderr={approve.stderr!r}"
        )
        # Sanity: the issue has moved to archive.
        assert (
            tmp_path
            / ".mantle"
            / "archive"
            / "issues"
            / "issue-50-test-issue.md"
        ).exists()

        review = _run_mantle(
            "save-review-result",
            "--issue",
            "50",
            "--feedback",
            "It works|approved|",
            cwd=tmp_path,
        )

        # Current contract: CLI must fail loudly, not silently succeed.
        assert review.returncode != 0, (
            "save-review-result silently succeeded after archival — "
            f"stdout={review.stdout!r} stderr={review.stderr!r}"
        )
        combined = (review.stdout + review.stderr).lower()
        assert "not found" in combined or "issue 50" in combined
        # And no review file was written.
        assert not (
            tmp_path / ".mantle" / "reviews" / "issue-50-review.md"
        ).exists()


class TestArchiveSideEffects:
    """find_issue_path and downstream commands after archive_issue."""

    def test_find_issue_path_returns_none_after_archive(
        self, tmp_path: Path
    ) -> None:
        _make_mantle_fixture(tmp_path, issue=50, issue_status="verified")
        # Archive directly via core — no transition required.
        moved = archive.archive_issue(tmp_path, 50)

        assert moved, "archive_issue returned no moved paths"
        # find_issue_path only looks at .mantle/issues/, not archive/.
        assert issues.find_issue_path(tmp_path, 50) is None

        mantle_dir = project.resolve_mantle_dir(tmp_path)
        archived = mantle_dir / "archive" / "issues" / "issue-50-test-issue.md"
        assert archived.exists()

    @pytest.mark.xfail(
        reason=(
            "save-learning does not call find_issue_path, so it silently"
            " writes a learning for an archived issue — see"
            " .mantle/inbox/ for the follow-up bug."
        ),
        strict=False,
    )
    def test_save_learning_after_archive_fails_clearly(
        self, tmp_path: Path
    ) -> None:
        _make_mantle_fixture(tmp_path, issue=50, issue_status="verified")
        archive.archive_issue(tmp_path, 50)

        result = _run_mantle(
            "save-learning",
            "--issue",
            "50",
            "--title",
            "After archive",
            "--confidence-delta",
            "+1",
            "--content",
            textwrap.dedent(
                """
                ## What Happened
                Archived issue.
                """
            ).strip(),
            cwd=tmp_path,
        )

        # Desired contract: command should fail clearly when the issue
        # it relates to has been archived, rather than silently writing
        # a learning into .mantle/learnings/.
        assert result.returncode != 0, (
            f"save-learning silently succeeded after archival:"
            f" stdout={result.stdout!r} stderr={result.stderr!r}"
        )
        combined = (result.stdout + result.stderr).lower()
        assert "not found" in combined or "archive" in combined

    def test_update_story_status_after_archive_fails_clearly(
        self, tmp_path: Path
    ) -> None:
        _make_mantle_fixture(tmp_path, issue=50, issue_status="verified")

        # Add a story so the archive has something to move.
        story_note = stories.StoryNote(
            issue=50,
            title="Test story",
            status="in-progress",
            tags=("type/story", "status/in-progress"),
        )
        story_path = (
            tmp_path / ".mantle" / "stories" / "issue-50-test-issue-story-01.md"
        )
        vault.write_note(story_path, story_note, "## User Story\n\nAs a ...\n")

        archive.archive_issue(tmp_path, 50)
        # Sanity check: story has moved to archive/stories/.
        assert not story_path.exists()

        result = _run_mantle(
            "update-story-status",
            "--issue",
            "50",
            "--story",
            "1",
            "--status",
            "completed",
            cwd=tmp_path,
        )

        assert result.returncode != 0, (
            f"update-story-status silently succeeded after archival:"
            f" stdout={result.stdout!r} stderr={result.stderr!r}"
        )
        combined = (result.stdout + result.stderr).lower()
        assert "not found" in combined
