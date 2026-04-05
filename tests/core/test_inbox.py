"""Tests for mantle.core.inbox."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from mantle.core import inbox, project

MOCK_EMAIL = "test@example.com"


@pytest.fixture(autouse=True)
def _mock_git(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock git identity for all tests in this module."""
    monkeypatch.setattr(
        "mantle.core.state.resolve_git_identity",
        lambda: MOCK_EMAIL,
    )


@pytest.fixture
def project_dir(tmp_path: Path) -> Path:
    """Create a minimal .mantle/ with inbox/ directory."""
    (tmp_path / ".mantle" / "inbox").mkdir(parents=True)
    return tmp_path


def _save_item(
    project_dir: Path,
    **overrides: object,
) -> tuple[inbox.InboxItem, Path]:
    """Save an inbox item with sensible defaults."""
    defaults: dict[str, object] = {
        "title": "Add dark mode support",
    }
    defaults.update(overrides)
    return inbox.save_inbox_item(project_dir, **defaults)


# ── save_inbox_item ────────────────────────────────────────────


class TestSaveInboxItem:
    def test_creates_file(self, project_dir: Path) -> None:
        _, path = _save_item(project_dir)

        assert path.exists()
        assert path.parent.name == "inbox"

    def test_correct_frontmatter(self, project_dir: Path) -> None:
        item, path = _save_item(project_dir)

        assert item.date == date.today()
        assert item.author == MOCK_EMAIL
        assert item.title == "Add dark mode support"
        assert item.source == "user"
        assert item.status == "open"

    def test_default_source(self, project_dir: Path) -> None:
        item, _ = _save_item(project_dir)

        assert item.source == "user"

    def test_ai_source(self, project_dir: Path) -> None:
        item, _ = _save_item(project_dir, source="ai")

        assert item.source == "ai"

    def test_invalid_source(self, project_dir: Path) -> None:
        with pytest.raises(ValueError, match="Invalid source"):
            _save_item(project_dir, source="web")

    def test_with_description(self, project_dir: Path) -> None:
        _, path = _save_item(
            project_dir,
            description="Users want a dark theme option.",
        )
        _, body = inbox.load_inbox_item(path)

        assert "Users want a dark theme option." in body

    def test_empty_description(self, project_dir: Path) -> None:
        _, path = _save_item(project_dir, description="")
        _, body = inbox.load_inbox_item(path)

        assert body == ""


# ── load_inbox_item ────────────────────────────────────────────


class TestLoadInboxItem:
    def test_round_trip(self, project_dir: Path) -> None:
        created, path = _save_item(project_dir)
        loaded, _ = inbox.load_inbox_item(path)

        assert loaded.date == created.date
        assert loaded.author == created.author
        assert loaded.title == created.title
        assert loaded.source == created.source
        assert loaded.status == created.status
        assert loaded.tags == created.tags


# ── list_inbox_items ───────────────────────────────────────────


class TestListInboxItems:
    def test_empty(self, project_dir: Path) -> None:
        result = inbox.list_inbox_items(project_dir)

        assert result == []

    def test_sorted_oldest_first(self, project_dir: Path) -> None:
        inbox_dir = project_dir / ".mantle" / "inbox"
        (inbox_dir / "2026-01-02-newer-idea.md").write_text(
            "---\ndate: 2026-01-02\nauthor: a@b.com\n"
            "title: Newer idea\nsource: user\nstatus: open\n"
            "tags:\n- type/inbox\n- status/open\n---\n"
        )
        (inbox_dir / "2026-01-01-older-idea.md").write_text(
            "---\ndate: 2026-01-01\nauthor: a@b.com\n"
            "title: Older idea\nsource: user\nstatus: open\n"
            "tags:\n- type/inbox\n- status/open\n---\n"
        )

        result = inbox.list_inbox_items(project_dir)

        assert len(result) == 2
        assert result[0].name < result[1].name
        assert result[0].name.startswith("2026-01-01")
        assert result[1].name.startswith("2026-01-02")

    def test_no_inbox_dir(self, tmp_path: Path) -> None:
        result = inbox.list_inbox_items(tmp_path)

        assert result == []

    def test_status_filter(self, project_dir: Path) -> None:
        _save_item(project_dir, title="Open idea")
        _save_item(project_dir, title="Promoted idea")
        items = inbox.list_inbox_items(project_dir)
        inbox.update_inbox_status(
            project_dir,
            items[1].name,
            status="promoted",
        )

        open_items = inbox.list_inbox_items(project_dir, status="open")
        promoted_items = inbox.list_inbox_items(
            project_dir, status="promoted"
        )

        assert len(open_items) == 1
        assert len(promoted_items) == 1


# ── update_inbox_status ────────────────────────────────────────


class TestUpdateInboxStatus:
    def test_promoted(self, project_dir: Path) -> None:
        _, path = _save_item(project_dir)
        updated, old_status = inbox.update_inbox_status(
            project_dir, path.name, status="promoted"
        )

        assert updated.status == "promoted"
        assert old_status == "open"

    def test_dismissed(self, project_dir: Path) -> None:
        _, path = _save_item(project_dir)
        updated, old_status = inbox.update_inbox_status(
            project_dir, path.name, status="dismissed"
        )

        assert updated.status == "dismissed"
        assert old_status == "open"

    def test_invalid_status(self, project_dir: Path) -> None:
        _, path = _save_item(project_dir)

        with pytest.raises(ValueError, match="Invalid status"):
            inbox.update_inbox_status(
                project_dir, path.name, status="invalid"
            )

    def test_updates_tag(self, project_dir: Path) -> None:
        _, path = _save_item(project_dir)
        updated, _ = inbox.update_inbox_status(
            project_dir, path.name, status="promoted"
        )

        assert "status/promoted" in updated.tags
        assert "status/open" not in updated.tags


# ── slug behavior (via public API) ────────────────────────────


class TestSlugBehavior:
    def test_spaces_to_hyphens_in_filename(
        self, project_dir: Path
    ) -> None:
        _, path = _save_item(project_dir, title="My Cool Idea!")

        assert "my-cool-idea" in path.name

    def test_long_title_slug_truncated(
        self, project_dir: Path
    ) -> None:
        long_title = "This is a very long title that exceeds thirty chars easily"
        _, path = _save_item(project_dir, title=long_title)

        # Date prefix is 10 chars plus hyphen = 11 chars total
        slug_part = path.stem[11:]

        assert len(slug_part) <= 30
        assert not slug_part.endswith("-")


class TestAutoIncrement:
    def test_collision_gets_suffix(self, project_dir: Path) -> None:
        _, path1 = _save_item(project_dir, title="My Idea")
        _, path2 = _save_item(project_dir, title="My Idea")

        assert path1.exists()
        assert path2.exists()
        assert path1 != path2
        assert path2.stem.endswith("-2")


# ── SUBDIRS ────────────────────────────────────────────────────


class TestSubdirs:
    def test_inbox_in_subdirs(self) -> None:
        assert "inbox" in project.SUBDIRS
