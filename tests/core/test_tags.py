"""Tests for mantle.core.tags."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from mantle.core.tags import add_tags, load_tags

SAMPLE_TAGS_MD = """\
---
tags:
- type/config
---

## Tag Taxonomy

### Type

- `type/idea`
- `type/skill`

### Status

- `status/active`
- `status/completed`

### Domain

- `domain/web`
"""


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """Create a minimal .mantle/ with a tags.md."""
    mantle = tmp_path / ".mantle"
    mantle.mkdir()
    (mantle / "tags.md").write_text(SAMPLE_TAGS_MD)
    return tmp_path


# ── load_tags ───────────────────────────────────────────────────


class TestLoadTags:
    """Tests for load_tags()."""

    def test_reads_tags(self, project: Path) -> None:
        result = load_tags(project)

        assert "type/idea" in result
        assert "type/skill" in result
        assert "status/active" in result
        assert "domain/web" in result

    def test_empty_when_no_file(self, tmp_path: Path) -> None:
        (tmp_path / ".mantle").mkdir()

        result = load_tags(tmp_path)

        assert result == set()


# ── add_tags ────────────────────────────────────────────────────


class TestAddTags:
    """Tests for add_tags()."""

    def test_new_tags_appended(self, project: Path) -> None:
        result = add_tags(project, ["domain/database"])

        assert result == ["domain/database"]

        # Verify it's now in the file.
        assert "domain/database" in load_tags(project)

    def test_existing_tags_skipped(self, project: Path) -> None:
        result = add_tags(project, ["domain/web"])

        assert result == []

    def test_creates_section(self, project: Path) -> None:
        result = add_tags(project, ["topic/python-asyncio"])

        assert result == ["topic/python-asyncio"]

        # Verify section was created and tag is loadable.
        tags = load_tags(project)
        assert "topic/python-asyncio" in tags

        # Verify the section heading exists in the file.
        text = (project / ".mantle" / "tags.md").read_text()
        assert "### Topic" in text
