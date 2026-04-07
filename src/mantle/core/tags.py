"""Tag taxonomy — read and update .mantle/tags.md."""

from __future__ import annotations

import dataclasses
import re
from typing import TYPE_CHECKING

from mantle.core import vault

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

_TAGS_PATH = ".mantle/tags.md"

# Map tag prefix to the section heading in tags.md.
_PREFIX_TO_SECTION: dict[str, str] = {
    "topic/": "Topic",
    "domain/": "Domain",
}


@dataclasses.dataclass(frozen=True)
class TagSummary:
    """Result of collecting tags from all sources.

    Attributes:
        taxonomy: Tags declared in .mantle/tags.md.
        vault: Tags found in vault skill frontmatter.
        undeclared: Tags in vault but not in taxonomy.
        by_prefix: All tags grouped by prefix
            (e.g. "Topic" -> ("topic/python",)).
    """

    taxonomy: frozenset[str]
    vault: frozenset[str]
    undeclared: frozenset[str]
    by_prefix: dict[str, tuple[str, ...]]


def load_tags(project_dir: Path) -> set[str]:
    """Read all tags from .mantle/tags.md.

    Parses inline-code tags (backtick-wrapped) from the tag taxonomy
    file. Lines like ``- `type/skill``` yield ``type/skill``.

    Args:
        project_dir: Directory containing .mantle/.

    Returns:
        Set of tag strings found in the file. Empty if the file
        has no tags or does not exist.
    """
    tags_path = project_dir / _TAGS_PATH
    if not tags_path.exists():
        return set()

    text = tags_path.read_text()
    return set(re.findall(r"`([^`]+/[^`]+)`", text))


def add_tags(
    project_dir: Path,
    new_tags: Sequence[str],
) -> list[str]:
    """Append new tags to the appropriate section in .mantle/tags.md.

    Infers the section from the tag prefix (e.g. ``topic/`` goes
    under the ``### Topic`` heading, ``domain/`` under ``### Domain``).
    Creates the section at the end of the file if it doesn't exist.
    Tags already present in the file are skipped.

    Args:
        project_dir: Directory containing .mantle/.
        new_tags: Tags to add.

    Returns:
        List of tags that were actually new (not already present).
    """
    tags_path = project_dir / _TAGS_PATH
    existing = load_tags(project_dir)

    actually_new = [t for t in new_tags if t not in existing]
    if not actually_new:
        return []

    text = tags_path.read_text() if tags_path.exists() else ""

    for tag in actually_new:
        section = _section_for_tag(tag)
        heading = f"### {section}"

        if heading in text:
            text = _append_to_section(text, heading, f"- `{tag}`")
        else:
            text = text.rstrip("\n") + f"\n\n{heading}\n\n- `{tag}`\n"

    tags_path.write_text(text)

    return actually_new


def _section_for_tag(tag: str) -> str:
    """Determine the tags.md section heading for a tag.

    Args:
        tag: A tag string like ``topic/python`` or ``domain/web``.

    Returns:
        Section name (e.g. ``"Topic"``, ``"Domain"``).
    """
    for prefix, section in _PREFIX_TO_SECTION.items():
        if tag.startswith(prefix):
            return section
    # Fall back to capitalised first segment.
    return tag.split("/")[0].capitalize()


def _append_to_section(text: str, heading: str, line: str) -> str:
    """Insert a line at the end of a section in markdown text.

    Finds the section by its heading and appends the line after
    the last non-empty line before the next heading or EOF.

    Args:
        text: Full markdown text.
        heading: The section heading to find (e.g. ``"### Topic"``).
        line: The line to append.

    Returns:
        Updated text with the line inserted.
    """
    lines = text.split("\n")
    heading_idx: int | None = None
    insert_idx: int | None = None

    for i, current in enumerate(lines):
        if current.strip() == heading:
            heading_idx = i
            continue
        if heading_idx is not None and current.startswith("### "):
            # Hit the next heading — insert before it.
            insert_idx = i
            break

    if heading_idx is not None and insert_idx is None:
        # Section runs to end of file — append after last non-empty line.
        insert_idx = len(lines)
        while insert_idx > heading_idx and not lines[insert_idx - 1].strip():
            insert_idx -= 1

    if insert_idx is not None:
        lines.insert(insert_idx, line)
        return "\n".join(lines)

    return text


def collect_all_tags(project_dir: Path) -> TagSummary:
    """Collect tags from taxonomy file and vault skill frontmatter.

    Merges tags from `.mantle/tags.md` (the declared taxonomy) with
    tags extracted from all vault skill frontmatter. Computes which
    vault tags are undeclared (present in skills but not in taxonomy)
    and groups all tags by prefix.

    Args:
        project_dir: Directory containing .mantle/.

    Returns:
        TagSummary with taxonomy, vault, undeclared, and grouped tags.
    """
    from mantle.core import skills

    taxonomy_tags: frozenset[str] = frozenset(load_tags(project_dir))

    try:
        skill_paths = skills.list_skills(project_dir)
    except skills.VaultNotConfiguredError, FileNotFoundError:
        vault_tags: frozenset[str] = frozenset()
    else:
        collected: set[str] = set()
        for path in skill_paths:
            try:
                note, _ = skills.load_skill(path)
            except (
                vault.NoteParseError,
                vault.NoteValidationError,
            ):
                continue
            collected.update(note.tags)
        vault_tags = frozenset(collected)

    undeclared = vault_tags - taxonomy_tags
    all_tags = taxonomy_tags | vault_tags

    groups: dict[str, list[str]] = {}
    for tag in all_tags:
        section = _section_for_tag(tag)
        groups.setdefault(section, []).append(tag)

    by_prefix: dict[str, tuple[str, ...]] = {
        section: tuple(sorted(tags)) for section, tags in sorted(groups.items())
    }

    return TagSummary(
        taxonomy=taxonomy_tags,
        vault=vault_tags,
        undeclared=undeclared,
        by_prefix=by_prefix,
    )
