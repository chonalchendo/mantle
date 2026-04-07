"""Tests for mantle.cli.main."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from mantle.core import project as project_module
from mantle.core import vault

if TYPE_CHECKING:
    from pathlib import Path

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

SAMPLE_TAGS_MD = """\
---
tags:
- type/config
---

### Topic

- `topic/python`

### Domain

- `domain/web`
"""


def _write_skill(skills_dir: Path, slug: str, skill_tags: list[str]) -> None:
    """Write a minimal skill file with given tags."""
    tag_lines = "\n".join(f"- {t}" for t in skill_tags)
    content = _SKILL_FRONTMATTER.format(name=slug, tags=tag_lines)
    skills_dir.mkdir(parents=True, exist_ok=True)
    (skills_dir / f"{slug}.md").write_text(content)


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """Create .mantle/ with tags.md and a vault with skill files."""
    mantle = tmp_path / ".mantle"
    mantle.mkdir()
    (mantle / "tags.md").write_text(SAMPLE_TAGS_MD)

    vault_path = tmp_path / "vault"
    skills_dir = vault_path / "skills"
    skills_dir.mkdir(parents=True)

    fm = project_module._ConfigFrontmatter(personal_vault=str(vault_path))
    vault.write_note(mantle / "config.md", fm, "## Config\n")

    _write_skill(
        skills_dir,
        "python",
        ["type/skill", "topic/python", "domain/web"],
    )

    return tmp_path


@pytest.fixture
def empty_project(tmp_path: Path) -> Path:
    """Create .mantle/ with no tags.md and no vault configured."""
    mantle = tmp_path / ".mantle"
    mantle.mkdir()

    fm = project_module._ConfigFrontmatter()
    vault.write_note(mantle / "config.md", fm, "## Config\n")

    return tmp_path


# ── list_tags_command ───────────────────────────────────────────


class TestListTagsCommand:
    """Tests for list-tags CLI command."""

    def test_list_tags_prints_grouped(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Tags from taxonomy and vault are printed grouped by prefix."""
        from mantle.cli.main import list_tags_command

        list_tags_command(path=project)
        captured = capsys.readouterr()

        out = captured.out
        assert "Domain:" in out
        assert "domain/web" in out
        assert "Topic:" in out
        assert "topic/python" in out
        assert out.index("Domain:") < out.index("domain/web")

    def test_list_tags_flags_undeclared(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Vault tags not in taxonomy show (undeclared) suffix."""
        vault_path = project / "vault"
        skills_dir = vault_path / "skills"

        # Add a skill with a tag not in taxonomy
        _write_skill(
            skills_dir,
            "docker",
            ["type/skill", "domain/devops"],
        )

        from mantle.cli.main import list_tags_command

        list_tags_command(path=project)
        captured = capsys.readouterr()

        assert "domain/devops" in captured.out
        assert "(undeclared)" in captured.out

    def test_list_tags_no_tags(
        self,
        empty_project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """No tags.md and no vault — prints 'No tags found.'"""
        from mantle.cli.main import list_tags_command

        list_tags_command(path=empty_project)
        captured = capsys.readouterr()

        assert "No tags found." in captured.out

    def test_list_tags_undeclared_footer(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Footer with count and suggestion when undeclared tags exist."""
        vault_path = project / "vault"
        skills_dir = vault_path / "skills"

        # Add a skill with undeclared tags
        _write_skill(
            skills_dir,
            "docker",
            ["type/skill", "domain/devops"],
        )

        from mantle.cli.main import list_tags_command

        list_tags_command(path=project)
        captured = capsys.readouterr()

        assert "undeclared tag" in captured.out
        assert ".mantle/tags.md" in captured.out
