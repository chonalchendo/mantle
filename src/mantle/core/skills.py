"""Skill graph — knowledge nodes with metadata in the personal vault."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING

import pydantic

from mantle.core import project, state, vault

if TYPE_CHECKING:
    from collections.abc import Sequence

_CONTENT_MARKER = "<!-- mantle:content -->"


# ── Data model ───────────────────────────────────────────────────


class SkillNote(pydantic.BaseModel, frozen=True):
    """Skill node frontmatter schema.

    Attributes:
        name: Human-readable skill name.
        description: What this skill covers and when it's relevant.
        type: Always "skill".
        proficiency: Self-assessment in "N/10" format.
        related_skills: Plain names of related skills (rendered as
            wikilinks in body).
        projects: Plain names of projects using this skill.
        last_used: Date the skill was last actively used.
        author: Git email of the skill author.
        created: Date the skill node was created.
        updated: Date of the last edit.
        updated_by: Git email of the last editor.
        tags: Mantle tags for categorization.
    """

    name: str
    description: str
    type: str = "skill"
    proficiency: str
    related_skills: tuple[str, ...] = ()
    projects: tuple[str, ...] = ()
    last_used: date
    author: str
    created: date
    updated: date
    updated_by: str
    tags: tuple[str, ...] = ("type/skill",)


# ── Exceptions ──────────────────────────────────────────────────


class VaultNotConfiguredError(Exception):
    """Raised when personal_vault is not set in config."""


class SkillExistsError(Exception):
    """Raised when the skill file already exists and overwrite is False.

    Attributes:
        path: Path to the existing skill file.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        super().__init__(f"Skill already exists: {path}")


# ── Internal helpers ─────────────────────────────────────────────


def _resolve_vault_skills_dir(project_dir: Path) -> Path:
    """Read personal_vault from config and return <vault>/skills/.

    Args:
        project_dir: Directory containing .mantle/.

    Returns:
        Path to the skills directory in the personal vault.

    Raises:
        VaultNotConfiguredError: If personal_vault is not configured.
    """
    config = project.read_config(project_dir)
    vault_path = config.get("personal_vault")
    if not vault_path:
        msg = (
            "Personal vault not configured. Run mantle init-vault <path> first."
        )
        raise VaultNotConfiguredError(msg)
    return Path(vault_path).expanduser().resolve() / "skills"


def _slugify(name: str) -> str:
    """Convert a skill name to a filename-safe slug.

    Args:
        name: Human-readable skill name.

    Returns:
        Lowercased, hyphenated slug.
    """
    slug = name.lower().replace(" ", "-")
    slug = re.sub(r"[^a-z0-9-]", "", slug)
    return slug


def _validate_proficiency(proficiency: str) -> None:
    """Check that proficiency matches "N/10" format.

    Args:
        proficiency: Proficiency string to validate.

    Raises:
        ValueError: If the format is invalid.
    """
    match = re.fullmatch(r"(\d+)/10", proficiency)
    if not match:
        msg = 'Invalid proficiency format. Use "N/10" (e.g. "7/10").'
        raise ValueError(msg)
    n = int(match.group(1))
    if n < 1 or n > 10:
        msg = 'Invalid proficiency format. Use "N/10" (e.g. "7/10").'
        raise ValueError(msg)


def _build_skill_body(note: SkillNote, content: str) -> str:
    """Build the full markdown body for a skill node.

    Prepends wikilink sections for related skills and projects,
    then includes the authored content verbatim.

    Args:
        note: The skill note with metadata.
        content: Authored skill knowledge (markdown).

    Returns:
        Complete markdown body string.
    """
    parts: list[str] = []

    if note.related_skills:
        links = "\n".join(f"- [[{s}]]" for s in note.related_skills)
        parts.append(f"## Related Skills\n\n{links}\n")

    if note.projects:
        links = "\n".join(f"- [[{p}]]" for p in note.projects)
        parts.append(f"## Projects\n\n{links}\n")

    parts.append(f"{_CONTENT_MARKER}\n{content}")

    return "\n".join(parts)


def _match_skill_slug(name: str, existing_paths: Sequence[Path]) -> Path | None:
    """Find a skill file matching the given name by slug comparison.

    Args:
        name: Human-readable skill name.
        existing_paths: List of existing skill file paths.

    Returns:
        The matching path, or None if no match.
    """
    target = _slugify(name)
    for path in existing_paths:
        if path.stem == target:
            return path
    return None


# ── Public API ───────────────────────────────────────────────────


def create_skill(
    project_dir: Path,
    *,
    name: str,
    description: str,
    proficiency: str,
    content: str,
    related_skills: tuple[str, ...] = (),
    projects: tuple[str, ...] = (),
    overwrite: bool = False,
) -> tuple[SkillNote, Path]:
    """Create a skill node in the personal vault.

    Args:
        project_dir: Directory containing .mantle/.
        name: Human-readable skill name.
        description: What this skill covers and when it's relevant.
        proficiency: Self-assessment in "N/10" format.
        content: Authored skill knowledge (markdown).
        related_skills: Related skill names.
        projects: Project names using this skill.
        overwrite: Replace existing skill if True.

    Returns:
        Tuple of (created SkillNote, path to the written file).

    Raises:
        VaultNotConfiguredError: If personal vault is not configured.
        SkillExistsError: If skill exists and overwrite is False.
        ValueError: If proficiency format is invalid.
    """
    _validate_proficiency(proficiency)

    skills_dir = _resolve_vault_skills_dir(project_dir)
    slug = _slugify(name)
    skill_path = skills_dir / f"{slug}.md"

    if skill_path.exists() and not overwrite:
        raise SkillExistsError(skill_path)

    identity = state.resolve_git_identity()
    today = date.today()

    note = SkillNote(
        name=name,
        description=description,
        proficiency=proficiency,
        related_skills=related_skills,
        projects=projects,
        last_used=today,
        author=identity,
        created=today,
        updated=today,
        updated_by=identity,
    )

    body = _build_skill_body(note, content)
    vault.write_note(skill_path, note, body)

    return note, skill_path


def load_skill(path: Path) -> tuple[SkillNote, str]:
    """Read a skill file and return frontmatter and body.

    Args:
        path: Absolute path to the skill markdown file.

    Returns:
        Tuple of (SkillNote frontmatter, body string).

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    note = vault.read_note(path, SkillNote)
    return note.frontmatter, note.body


def list_skills(project_dir: Path) -> list[Path]:
    """List all skill paths in the personal vault.

    Args:
        project_dir: Directory containing .mantle/.

    Returns:
        Alphabetically sorted list of skill file paths.

    Raises:
        VaultNotConfiguredError: If personal vault is not configured.
    """
    skills_dir = _resolve_vault_skills_dir(project_dir)
    if not skills_dir.exists():
        return []
    return sorted(skills_dir.glob("*.md"))


def skill_exists(project_dir: Path, name: str) -> bool:
    """Check whether a skill node exists in the vault.

    Args:
        project_dir: Directory containing .mantle/.
        name: Human-readable skill name.

    Returns:
        True if the skill file exists, False otherwise.

    Raises:
        VaultNotConfiguredError: If personal vault is not configured.
    """
    skills_dir = _resolve_vault_skills_dir(project_dir)
    slug = _slugify(name)
    return (skills_dir / f"{slug}.md").exists()


def update_skill(
    project_dir: Path,
    name: str,
    *,
    description: str | None = None,
    proficiency: str | None = None,
    content: str | None = None,
    related_skills: tuple[str, ...] | None = None,
    projects: tuple[str, ...] | None = None,
) -> SkillNote:
    """Update fields on an existing skill node.

    Args:
        project_dir: Directory containing .mantle/.
        name: Human-readable skill name (used to find the file).
        description: New description, or None to keep current.
        proficiency: New proficiency, or None to keep current.
        content: New authored content, or None to keep current.
        related_skills: New related skills, or None to keep current.
        projects: New projects, or None to keep current.

    Returns:
        The updated SkillNote.

    Raises:
        FileNotFoundError: If the skill file does not exist.
        VaultNotConfiguredError: If personal vault is not configured.
        ValueError: If proficiency format is invalid.
    """
    skills_dir = _resolve_vault_skills_dir(project_dir)
    slug = _slugify(name)
    skill_path = skills_dir / f"{slug}.md"

    if not skill_path.exists():
        msg = f"Skill not found: {skill_path}"
        raise FileNotFoundError(msg)

    if proficiency is not None:
        _validate_proficiency(proficiency)

    current_note, current_body = load_skill(skill_path)
    identity = state.resolve_git_identity()
    today = date.today()

    updates: dict[str, object] = {
        "updated": today,
        "updated_by": identity,
        "last_used": today,
    }
    if description is not None:
        updates["description"] = description
    if proficiency is not None:
        updates["proficiency"] = proficiency
    if related_skills is not None:
        updates["related_skills"] = related_skills
    if projects is not None:
        updates["projects"] = projects

    updated_note = current_note.model_copy(update=updates)

    # Determine content for the body
    if content is not None:
        new_content = content
    else:
        new_content = _extract_content(current_body)

    body = _build_skill_body(updated_note, new_content)
    vault.write_note(skill_path, updated_note, body)

    return updated_note


def _extract_content(body: str) -> str:
    """Extract the authored content from a skill body.

    Splits on the ``<!-- mantle:content -->`` marker inserted by
    :func:`_build_skill_body`.  Falls back to returning the full
    body if no marker is present (e.g. hand-edited files).

    Args:
        body: Full skill body markdown.

    Returns:
        The authored content portion.
    """
    if _CONTENT_MARKER in body:
        _, content = body.split(_CONTENT_MARKER, maxsplit=1)
        return content.lstrip("\n")
    return body


# ── Gap detection and skill loading ──────────────────────────────


def detect_gaps(project_dir: Path) -> list[str]:
    """Find skills_required that have no matching node in the vault.

    Compares ``skills_required`` from ``state.md`` against existing
    skill files using slug-normalized, case-insensitive matching.

    Args:
        project_dir: Directory containing .mantle/.

    Returns:
        List of unmatched skill names from ``skills_required``.
        Empty if all are tracked or none are required.

    Raises:
        VaultNotConfiguredError: If personal vault is not configured.
    """
    current_state = state.load_state(project_dir)
    required = current_state.skills_required
    if not required:
        return []

    existing = list_skills(project_dir)
    gaps: list[str] = []
    for name in required:
        if _match_skill_slug(name, existing) is None:
            gaps.append(name)
    return gaps


def suggest_gap_message(gaps: Sequence[str]) -> str:
    """Format a human-readable message listing untracked skills.

    Args:
        gaps: List of unmatched skill names.

    Returns:
        Formatted message string, or empty string if no gaps.
    """
    if not gaps:
        return ""
    items = "\n".join(f"  - {g}" for g in gaps)
    return (
        f"Untracked skills detected:\n"
        f"{items}\n"
        f"\n"
        f"Run /mantle:add-skill to create skill nodes for these.\n"
    )


def load_relevant_skills(
    project_dir: Path,
) -> list[tuple[SkillNote, str]]:
    """Load skill nodes matching skills_required from state.

    For each required skill with a matching vault node, loads the
    full note (frontmatter + body). The body contains authored
    knowledge written for Claude's consumption. Missing skills are
    silently skipped — use :func:`detect_gaps` to surface them.

    Args:
        project_dir: Directory containing .mantle/.

    Returns:
        List of ``(SkillNote, body)`` tuples for matched skills.

    Raises:
        VaultNotConfiguredError: If personal vault is not configured.
    """
    current_state = state.load_state(project_dir)
    required = current_state.skills_required
    if not required:
        return []

    existing = list_skills(project_dir)
    results: list[tuple[SkillNote, str]] = []
    for name in required:
        match = _match_skill_slug(name, existing)
        if match is not None:
            note, body = load_skill(match)
            results.append((note, body))
    return results
