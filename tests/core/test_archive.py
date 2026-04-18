"""Tests for mantle.core.archive."""

from __future__ import annotations

from typing import TYPE_CHECKING

from mantle.core import archive

if TYPE_CHECKING:
    from pathlib import Path


# ── Helpers ─────────────────────────────────────────────────────


def _setup_mantle(tmp_path: Path, issue: int = 1) -> None:
    """Create a minimal .mantle/ with issue, stories, shaped, learning."""
    mantle = tmp_path / ".mantle"
    for subdir in ("issues", "stories", "shaped", "learnings"):
        (mantle / subdir).mkdir(parents=True)

    # Issue file
    (mantle / "issues" / f"issue-{issue:02d}-test-issue.md").write_text(
        "---\ntitle: Test issue\nstatus: approved\n"
        "slice: [core]\ntags: [type/issue]\n---\nBody\n"
    )
    # Two stories
    for s in (1, 2):
        (
            mantle
            / "stories"
            / f"issue-{issue:02d}-test-issue-story-{s:02d}.md"
        ).write_text(
            f"---\nissue: {issue}\ntitle: Story {s}\nstatus: completed\n"
            f"tags: [type/story]\n---\nBody\n"
        )
    # Shaped doc
    (mantle / "shaped" / f"issue-{issue:02d}-test-issue-shaped.md").write_text(
        "---\ntitle: Shaped\n---\nApproach\n"
    )
    # Learning
    (mantle / "learnings" / f"issue-{issue:02d}-test-issue.md").write_text(
        "---\nissue: 1\ntitle: Test\n---\nLearning\n"
    )


# ── Tests ───────────────────────────────────────────────────────


class TestArchiveIssue:
    """Tests for archive_issue."""

    def test_moves_all_artifacts(self, tmp_path: Path) -> None:
        _setup_mantle(tmp_path)
        moved = archive.archive_issue(tmp_path, 1)

        assert len(moved) == 5  # 1 issue + 2 stories + 1 shaped + 1 learning

        archive_dir = tmp_path / ".mantle" / "archive"
        assert (archive_dir / "issues" / "issue-01-test-issue.md").exists()
        assert (
            archive_dir / "stories" / "issue-01-test-issue-story-01.md"
        ).exists()
        assert (
            archive_dir / "stories" / "issue-01-test-issue-story-02.md"
        ).exists()
        assert (
            archive_dir / "shaped" / "issue-01-test-issue-shaped.md"
        ).exists()
        assert (archive_dir / "learnings" / "issue-01-test-issue.md").exists()

    def test_source_files_removed(self, tmp_path: Path) -> None:
        _setup_mantle(tmp_path)
        archive.archive_issue(tmp_path, 1)

        mantle = tmp_path / ".mantle"
        assert not list(mantle.glob("issues/issue-01-*.md"))
        assert not list(mantle.glob("stories/issue-01-*.md"))
        assert not list(mantle.glob("shaped/issue-01-*.md"))
        assert not list(mantle.glob("learnings/issue-01-*.md"))

    def test_no_files_returns_empty(self, tmp_path: Path) -> None:
        mantle = tmp_path / ".mantle"
        (mantle / "issues").mkdir(parents=True)
        moved = archive.archive_issue(tmp_path, 99)

        assert moved == []
        assert not (mantle / "archive").exists()

    def test_partial_artifacts(self, tmp_path: Path) -> None:
        """Archive works when only some artifact types exist."""
        mantle = tmp_path / ".mantle"
        (mantle / "issues").mkdir(parents=True)
        (mantle / "issues" / "issue-02-partial.md").write_text(
            "---\ntitle: Partial\nstatus: approved\n"
            "slice: [core]\ntags: [type/issue]\n---\n"
        )

        moved = archive.archive_issue(tmp_path, 2)

        assert len(moved) == 1
        assert (mantle / "archive" / "issues" / "issue-02-partial.md").exists()

    def test_slug_less_shaped_doc_is_archived(self, tmp_path: Path) -> None:
        """Archive matches shaped docs with no slug (issue-NN-shaped.md)."""
        mantle = tmp_path / ".mantle"
        (mantle / "issues").mkdir(parents=True)
        (mantle / "shaped").mkdir(parents=True)

        (mantle / "issues" / "issue-24-slug-less.md").write_text(
            "---\ntitle: Slug-less\nstatus: approved\n"
            "slice: [core]\ntags: [type/issue]\n---\nBody\n"
        )
        (mantle / "shaped" / "issue-24-shaped.md").write_text(
            "---\ntitle: Shaped\n---\nApproach\n"
        )

        moved = archive.archive_issue(tmp_path, 24)

        assert len(moved) == 2
        archive_dir = mantle / "archive"
        assert (archive_dir / "shaped" / "issue-24-shaped.md").exists()
        assert not (mantle / "shaped" / "issue-24-shaped.md").exists()
