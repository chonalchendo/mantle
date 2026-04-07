"""Tests for mantle.core.tags."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from mantle.core import tags

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

_SKILL_FRONTMATTER = """\
---
name: {name}
description: A test skill.
type: skill
proficiency: 5/10
last_used: 2024-01-01
author: test@example.com
created: 2024-01-01
updated: 2024-01-01
updated_by: test@example.com
tags:
{tags}
---

## Context

Test skill content.
"""


def _write_skill(skills_dir: Path, slug: str, skill_tags: list[str]) -> None:
    """Write a minimal skill file with given tags to skills_dir."""
    tag_lines = "\n".join(f"- {t}" for t in skill_tags)
    content = _SKILL_FRONTMATTER.format(name=slug, tags=tag_lines)
    skills_dir.mkdir(parents=True, exist_ok=True)
    (skills_dir / f"{slug}.md").write_text(content)


def _write_config(mantle: Path, personal_vault: str | None) -> None:
    """Write a minimal config.md with the given personal_vault value."""
    vault_value = (
        f"personal_vault: {personal_vault}"
        if personal_vault is not None
        else "personal_vault: null"
    )
    content = f"""\
---
{vault_value}
verification_strategy: null
auto_push: false
tags:
- type/config
---

## Config
"""
    (mantle / "config.md").write_text(content)


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """Create a minimal .mantle/ with a tags.md."""
    mantle = tmp_path / ".mantle"
    mantle.mkdir()
    (mantle / "tags.md").write_text(SAMPLE_TAGS_MD)
    return tmp_path


@pytest.fixture
def vault_project(tmp_path: Path) -> Path:
    """Create .mantle/ with tags.md and a vault with skill files."""
    mantle = tmp_path / ".mantle"
    mantle.mkdir()

    # Write tags.md with taxonomy
    (mantle / "tags.md").write_text("""\
---
tags:
- type/config
---

### Type

- `type/skill`

### Domain

- `domain/web`
""")

    # Set up vault with skills directory
    vault_path = tmp_path / "vault"
    skills_dir = vault_path / "skills"
    skills_dir.mkdir(parents=True)

    # Write config.md pointing to vault
    _write_config(mantle, str(vault_path))

    # Write a skill with tags some in taxonomy, some not
    _write_skill(
        skills_dir,
        "python",
        ["type/skill", "topic/python", "domain/web"],
    )

    return tmp_path


# ── load_tags ───────────────────────────────────────────────────


class TestLoadTags:
    """Tests for load_tags()."""

    def test_reads_tags(self, project: Path) -> None:
        result = tags.load_tags(project)

        assert "type/idea" in result
        assert "type/skill" in result
        assert "status/active" in result
        assert "domain/web" in result

    def test_empty_when_no_file(self, tmp_path: Path) -> None:
        (tmp_path / ".mantle").mkdir()

        result = tags.load_tags(tmp_path)

        assert result == set()


# ── add_tags ────────────────────────────────────────────────────


class TestAddTags:
    """Tests for add_tags()."""

    def test_new_tags_appended(self, project: Path) -> None:
        result = tags.add_tags(project, ["domain/database"])

        assert result == ["domain/database"]

        # Verify it's now in the file.
        assert "domain/database" in tags.load_tags(project)

    def test_existing_tags_skipped(self, project: Path) -> None:
        result = tags.add_tags(project, ["domain/web"])

        assert result == []

    def test_creates_section(self, project: Path) -> None:
        result = tags.add_tags(project, ["topic/python-asyncio"])

        assert result == ["topic/python-asyncio"]

        # Verify section was created and tag is loadable.
        loaded = tags.load_tags(project)
        assert "topic/python-asyncio" in loaded

        # Verify the section heading exists in the file.
        text = (project / ".mantle" / "tags.md").read_text()
        assert "### Topic" in text


# ── collect_all_tags ─────────────────────────────────────────────


class TestCollectAllTags:
    """Tests for collect_all_tags()."""

    def test_collect_all_tags_merges_sources(self, vault_project: Path) -> None:
        """Taxonomy and vault tags are both present in the result."""
        result = tags.collect_all_tags(vault_project)

        # Taxonomy tags
        assert "type/skill" in result.taxonomy
        assert "domain/web" in result.taxonomy

        # Vault tags (from the python skill)
        assert "type/skill" in result.vault
        assert "topic/python" in result.vault
        assert "domain/web" in result.vault

        # Undeclared: in vault but not in taxonomy
        assert "topic/python" in result.undeclared
        # type/skill and domain/web ARE in taxonomy, so not undeclared
        assert "type/skill" not in result.undeclared
        assert "domain/web" not in result.undeclared

    def test_collect_all_tags_groups_by_prefix(
        self, vault_project: Path
    ) -> None:
        """Tags are grouped by prefix correctly."""
        result = tags.collect_all_tags(vault_project)

        assert "Topic" in result.by_prefix
        assert "topic/python" in result.by_prefix["Topic"]

        assert "Domain" in result.by_prefix
        assert "domain/web" in result.by_prefix["Domain"]

        assert "Type" in result.by_prefix
        assert "type/skill" in result.by_prefix["Type"]

    def test_collect_all_tags_no_vault(self, tmp_path: Path) -> None:
        """No vault configured — returns taxonomy tags only."""
        mantle = tmp_path / ".mantle"
        mantle.mkdir()
        (mantle / "tags.md").write_text("""\
---
tags:
- type/config
---

### Type

- `type/skill`
""")
        # Write a config.md with no vault configured
        _write_config(mantle, None)

        result = tags.collect_all_tags(tmp_path)

        assert result.taxonomy == frozenset({"type/skill"})
        assert result.vault == frozenset()
        assert result.undeclared == frozenset()

    def test_collect_all_tags_no_taxonomy_file(self, tmp_path: Path) -> None:
        """No tags.md — all vault tags are undeclared."""
        mantle = tmp_path / ".mantle"
        mantle.mkdir()

        vault_path = tmp_path / "vault"
        skills_dir = vault_path / "skills"
        skills_dir.mkdir(parents=True)

        _write_config(mantle, str(vault_path))

        _write_skill(skills_dir, "python", ["type/skill", "topic/python"])

        result = tags.collect_all_tags(tmp_path)

        assert result.taxonomy == frozenset()
        assert "topic/python" in result.vault
        assert "type/skill" in result.vault
        # All vault tags are undeclared when no taxonomy exists
        assert result.undeclared == result.vault

    def test_collect_all_tags_no_config_file(self, tmp_path: Path) -> None:
        """No tags.md and no vault — returns empty TagSummary."""
        mantle = tmp_path / ".mantle"
        mantle.mkdir()
        # No config.md — VaultNotConfiguredError expected and handled

        result = tags.collect_all_tags(tmp_path)

        assert result.taxonomy == frozenset()
        assert result.vault == frozenset()
        assert result.undeclared == frozenset()
        assert result.by_prefix == {}

    def test_collect_all_tags_skips_unparseable_skills(
        self, tmp_path: Path
    ) -> None:
        """Malformed skill files are silently skipped."""
        mantle = tmp_path / ".mantle"
        mantle.mkdir()

        vault_path = tmp_path / "vault"
        skills_dir = vault_path / "skills"
        skills_dir.mkdir(parents=True)

        _write_config(mantle, str(vault_path))

        # Write a valid skill
        _write_skill(skills_dir, "python", ["type/skill", "topic/python"])

        # Write a malformed skill (invalid YAML frontmatter)
        (skills_dir / "broken.md").write_text(
            "---\n: invalid: yaml: [\n---\n\nContent.\n"
        )

        result = tags.collect_all_tags(tmp_path)

        # Valid skill's tags should be present
        assert "topic/python" in result.vault
        # No exception raised — broken file was skipped
