"""Skill graph — knowledge nodes with metadata in the personal vault."""

from __future__ import annotations

import re
import shutil
import warnings
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING

import pydantic
import yaml

from mantle.core import project, state, vault

if TYPE_CHECKING:
    from collections.abc import Sequence

_CONTENT_MARKER = "<!-- mantle:content -->"
_GENERATED_MARKER = "<!-- mantle:generated -->"

_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "and",
        "or",
        "not",
        "this",
        "that",
        "it",
        "by",
        "from",
        "as",
    }
)


def _tokenize(text: str) -> set[str]:
    """Split text into lowercase word tokens."""
    return {t for t in re.split(r"[^a-z0-9]+", text.lower()) if t}


# ── Data model ───────────────────────────────────────────────────


class SkillNote(pydantic.BaseModel, frozen=True):
    """Skill node frontmatter schema.

    Attributes:
        name: Human-readable skill name.
        description: What this skill covers and when it's relevant.
        when_to_use: Trigger conditions for auto-invocation, separate
            from the description.  Used during compilation to generate
            the ``TRIGGER when`` line.  Falls back to ``description``
            when empty.
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
    when_to_use: str = ""
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


class SkillSummary(pydantic.BaseModel, frozen=True):
    """Lightweight skill descriptor for selection UIs.

    Attributes:
        slug: Filename stem identifying the skill.
        description: What this skill covers and when it's relevant.
    """

    slug: str
    description: str


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
    if n < 0 or n > 10:
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
        links = "\n".join(
            f"- [[{_slugify(s)}|{s}]]" for s in note.related_skills
        )
        parts.append(f"## Related Skills\n\n{links}\n")

    if note.projects:
        links = "\n".join(
            f"- [[projects/{_slugify(p)}|{p}]]" for p in note.projects
        )
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


def _match_required_skills(
    project_dir: Path,
    skills_filter: tuple[str, ...] = (),
) -> list[tuple[str, Path | None]]:
    """Match ``skills_required`` names to vault paths.

    Loads state and vault skill list once, then matches each required
    skill name by slug.  When ``skills_filter`` is provided, it is
    used instead of the ``skills_required`` from ``state.md``.

    Args:
        project_dir: Directory containing ``.mantle/``.
        skills_filter: Explicit skill names to match.  When non-empty,
            overrides the ``skills_required`` from ``state.md``.

    Returns:
        List of ``(required name, matched path or None)`` pairs.

    Raises:
        VaultNotConfiguredError: If personal vault is not configured.
    """
    required = skills_filter or state.load_state(project_dir).skills_required
    if not required:
        return []
    existing = list_skills(project_dir)
    return [(name, _match_skill_slug(name, existing)) for name in required]


def _ensure_type_skill(tags: Sequence[str]) -> tuple[str, ...]:
    """Ensure ``type/skill`` is present in the tags tuple.

    Args:
        tags: Input tag sequence.

    Returns:
        Tuple with ``type/skill`` guaranteed to be included.
    """
    result = list(tags)
    if "type/skill" not in result:
        result.insert(0, "type/skill")
    return tuple(result)


# ── Public API ───────────────────────────────────────────────────


def create_skill(
    project_dir: Path,
    *,
    name: str,
    description: str,
    proficiency: str,
    content: str,
    when_to_use: str = "",
    related_skills: tuple[str, ...] = (),
    projects: tuple[str, ...] = (),
    tags: tuple[str, ...] = (),
    overwrite: bool = False,
) -> tuple[SkillNote, Path]:
    """Create a skill node in the personal vault.

    Args:
        project_dir: Directory containing .mantle/.
        name: Human-readable skill name.
        description: What this skill covers and when it's relevant.
        proficiency: Self-assessment in "N/10" format.
        content: Authored skill knowledge (markdown).
        when_to_use: Trigger conditions for auto-invocation.
        related_skills: Related skill names.
        projects: Project names using this skill.
        tags: Content tags. ``type/skill`` is always included.
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
        when_to_use=when_to_use,
        proficiency=proficiency,
        related_skills=related_skills,
        projects=projects,
        tags=_ensure_type_skill(tags),
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


def list_skills(
    project_dir: Path,
    *,
    tag: str | None = None,
) -> list[Path]:
    """List all skill paths in the personal vault.

    Args:
        project_dir: Directory containing .mantle/.
        tag: Optional tag to filter by (e.g. ``topic/python``).
            When provided, only skills whose ``tags`` tuple contains
            this value are returned.  Unparseable skill files are
            silently skipped.

    Returns:
        Alphabetically sorted list of skill file paths.

    Raises:
        VaultNotConfiguredError: If personal vault is not configured.
    """
    skills_dir = _resolve_vault_skills_dir(project_dir)
    if not skills_dir.exists():
        return []
    all_paths = sorted(skills_dir.glob("*.md"))
    if tag is None:
        return all_paths
    filtered: list[Path] = []
    for path in all_paths:
        try:
            note, _ = load_skill(path)
        except vault.NoteParseError, vault.NoteValidationError:
            continue
        if tag in note.tags:
            filtered.append(path)
    return filtered


def list_skill_summaries(
    project_dir: Path,
    *,
    tag: str | None = None,
) -> list[SkillSummary]:
    """Return slug and description for all vault skills.

    Args:
        project_dir: Directory containing .mantle/.
        tag: Optional tag to filter by.

    Returns:
        Alphabetically sorted list of SkillSummary.

    Raises:
        VaultNotConfiguredError: If personal vault is not configured.
    """
    paths = list_skills(project_dir, tag=tag)
    summaries: list[SkillSummary] = []
    for path in paths:
        try:
            note, _ = load_skill(path)
        except vault.NoteParseError, vault.NoteValidationError:
            continue
        summaries.append(
            SkillSummary(slug=path.stem, description=note.description)
        )
    return summaries


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


def validate_related_skills(
    project_dir: Path,
    related_skills: Sequence[str],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Check which related skills exist in the vault.

    Args:
        project_dir: Directory containing .mantle/.
        related_skills: Skill names to check.

    Returns:
        Tuple of (existing, missing) skill name tuples.

    Raises:
        VaultNotConfiguredError: If personal vault is not configured.
    """
    existing: list[str] = []
    missing: list[str] = []
    for name in related_skills:
        if skill_exists(project_dir, name):
            existing.append(name)
        else:
            missing.append(name)
    return tuple(existing), tuple(missing)


def create_stub_skill(
    project_dir: Path,
    name: str,
) -> Path:
    """Create a minimal stub skill node in the vault.

    Stub skills have proficiency 0/10 and a placeholder context
    section, intended to be fleshed out later via /mantle:add-skill.

    Args:
        project_dir: Directory containing .mantle/.
        name: Human-readable skill name.

    Returns:
        Path to the created stub file.

    Raises:
        VaultNotConfiguredError: If personal vault is not configured.
        SkillExistsError: If the skill already exists.
    """
    _, path = create_skill(
        project_dir,
        name=name,
        description=f"Stub for {name}. Flesh out via /mantle:add-skill.",
        proficiency="0/10",
        content="## Context\n\nTODO: Add skill knowledge.",
    )
    return path


def update_skill(
    project_dir: Path,
    name: str,
    *,
    description: str | None = None,
    when_to_use: str | None = None,
    proficiency: str | None = None,
    content: str | None = None,
    related_skills: tuple[str, ...] | None = None,
    projects: tuple[str, ...] | None = None,
    tags: tuple[str, ...] | None = None,
) -> SkillNote:
    """Update fields on an existing skill node.

    Args:
        project_dir: Directory containing .mantle/.
        name: Human-readable skill name (used to find the file).
        description: New description, or None to keep current.
        when_to_use: New trigger conditions, or None to keep current.
        proficiency: New proficiency, or None to keep current.
        content: New authored content, or None to keep current.
        related_skills: New related skills, or None to keep current.
        projects: New projects, or None to keep current.
        tags: New tags, or None to keep current. ``type/skill``
            is always included.

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
    if when_to_use is not None:
        updates["when_to_use"] = when_to_use
    if proficiency is not None:
        updates["proficiency"] = proficiency
    if related_skills is not None:
        updates["related_skills"] = related_skills
    if projects is not None:
        updates["projects"] = projects
    if tags is not None:
        updates["tags"] = _ensure_type_skill(tags)

    updated_note = current_note.model_copy(update=updates)

    new_content = (
        content if content is not None else _extract_content(current_body)
    )

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
    return [
        name
        for name, path in _match_required_skills(project_dir)
        if path is None
    ]


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


def detect_stubs(project_dir: Path) -> list[tuple[str, Path]]:
    """Find ``skills_required`` that exist as stubs (0/10 proficiency).

    Args:
        project_dir: Directory containing ``.mantle/``.

    Returns:
        List of ``(skill name, path)`` tuples for stub skills that
        are in ``skills_required`` and have proficiency ``"0/10"``.

    Raises:
        VaultNotConfiguredError: If personal vault is not configured.
    """
    stubs: list[tuple[str, Path]] = []
    for _, path in _match_required_skills(project_dir):
        if path is not None:
            note, _ = load_skill(path)
            if note.proficiency == "0/10":
                stubs.append((note.name, path))
    return stubs


def suggest_stub_message(stubs: Sequence[tuple[str, Path]]) -> str:
    """Format a message prompting the user to fill stub skills.

    Args:
        stubs: List of ``(skill name, path)`` tuples.

    Returns:
        Formatted message string, or empty string if no stubs.
    """
    if not stubs:
        return ""
    items = "\n".join(f"  - {name} (0/10)" for name, _ in stubs)
    return (
        "Stub skills detected that could be fleshed out:\n"
        f"{items}\n"
        "\n"
        "Run /mantle:add-skill to add your knowledge to these.\n"
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
    return [
        load_skill(path)
        for _, path in _match_required_skills(project_dir)
        if path is not None
    ]


# ── Auto-detection ─────────────────────────────────────────────


def detect_skills_from_content(
    project_dir: Path,
    content: str,
) -> list[str]:
    """Extract skill references from markdown content by matching vault skills.

    Scans the content for vault skill names (case-insensitive) and returns
    matched skill names. Only matches skills that exist in the vault.

    Args:
        project_dir: Directory containing .mantle/.
        content: Markdown content to scan (e.g., issue or story body).

    Returns:
        List of matched skill names from the vault.

    Raises:
        VaultNotConfiguredError: If personal vault is not configured.
    """
    existing = list_skills(project_dir)
    if not existing:
        return []

    content_lower = content.lower()
    content_tokens = _tokenize(content_lower)
    matched: list[str] = []

    for path in existing:
        try:
            note, _ = load_skill(path)
        except vault.NoteParseError, vault.NoteValidationError:
            continue
        # Match by name (case-insensitive)
        if note.name.lower() in content_lower:
            matched.append(note.name)
            continue
        # Match by slug (e.g., "python-asyncio" in code blocks)
        if path.stem in content_lower:
            matched.append(note.name)
            continue
        # Match by tag suffix (filter out type/ tags)
        tag_suffixes = [
            t.split("/")[-1] for t in note.tags if not t.startswith("type/")
        ]
        if any(
            re.search(rf"\b{re.escape(s)}\b", content_lower)
            for s in tag_suffixes
        ):
            matched.append(note.name)
            continue
        # Match by description word overlap (3+ non-stopword tokens)
        desc_tokens = _tokenize(note.description) - _STOPWORDS
        if len(desc_tokens & content_tokens) >= 3:
            matched.append(note.name)

    return matched


def auto_update_skills(
    project_dir: Path,
    issue_number: int,
) -> list[str]:
    """Auto-detect and update skills_required from issue and story content.

    Reads the issue and all its stories, detects vault skill matches,
    and merges them into ``skills_required`` in ``state.md``.

    Args:
        project_dir: Directory containing .mantle/.
        issue_number: Issue number to scan.

    Returns:
        List of newly detected skill names (not previously in
        skills_required).

    Raises:
        VaultNotConfiguredError: If personal vault is not configured.
    """
    mantle_dir = project.resolve_mantle_dir(project_dir)

    # Collect all content from issue and its stories
    content_parts: list[str] = []

    # Match both "issue-01.md" and "issue-01-title.md" naming conventions
    issues_dir = mantle_dir / "issues"
    if issues_dir.exists():
        prefix = f"issue-{issue_number:02d}"
        for p in issues_dir.glob("*.md"):
            if p.stem == prefix or p.stem.startswith(f"{prefix}-"):
                content_parts.append(p.read_text(encoding="utf-8"))

    stories_dir = mantle_dir / "stories"
    if stories_dir.exists():
        for story_path in sorted(stories_dir.glob("*.md")):
            if story_path.stem.startswith(f"issue-{issue_number:02d}"):
                content_parts.append(story_path.read_text(encoding="utf-8"))

    shaped_dir = mantle_dir / "shaped"
    if shaped_dir.exists():
        for p in shaped_dir.glob("*.md"):
            if p.stem.startswith(f"issue-{issue_number:02d}"):
                content_parts.append(p.read_text(encoding="utf-8"))

    if not content_parts:
        return []

    combined = "\n".join(content_parts)
    detected = detect_skills_from_content(project_dir, combined)

    if not detected:
        return []

    # Determine which are new
    current_state = state.load_state(project_dir)
    existing = set(current_state.skills_required)
    new_skills = [s for s in detected if s not in existing]

    if new_skills:
        state.update_skills_required(
            project_dir,
            tuple(detected),
            additive=True,
        )

    # Also update the issue file's skills_required
    # Local import to avoid circular dependency:
    # issues -> state <- skills -> issues
    from mantle.core import issues as issues_mod

    issue_path = issues_mod.find_issue_path(project_dir, issue_number)
    if issue_path is not None:
        try:
            issue_note, issue_body = issues_mod.load_issue(issue_path)
        except vault.NoteParseError, vault.NoteValidationError:
            return new_skills
        merged = set(issue_note.skills_required) | set(detected)
        if merged != set(issue_note.skills_required):
            updated_note = issue_note.model_copy(
                update={
                    "skills_required": tuple(sorted(merged)),
                },
            )
            vault.write_note(issue_path, updated_note, issue_body)

    return new_skills


# ── Index generation ────────────────────────────────────────────


def generate_index_notes(project_dir: Path) -> list[str]:
    """Generate index notes in the vault for each non-type tag.

    Reads all skills from the vault, groups them by tag (excluding
    tags that start with ``type/``), and writes one index note per
    tag under ``<vault>/indexes/<tag-slug>.md``.

    Existing files that do not contain the generated marker are left
    untouched so that manually-maintained index notes are preserved.

    Args:
        project_dir: Directory containing ``.mantle/``.

    Returns:
        List of tag strings for which index notes were written.

    Raises:
        VaultNotConfiguredError: If personal vault is not configured.
    """
    skill_paths = list_skills(project_dir)
    tag_to_slugs: dict[str, list[str]] = {}

    for path in skill_paths:
        try:
            note, _ = load_skill(path)
        except vault.NoteParseError, vault.NoteValidationError:
            continue
        for tag in note.tags:
            if tag.startswith("type/"):
                continue
            tag_to_slugs.setdefault(tag, []).append(path.stem)

    vault_root = _resolve_vault_skills_dir(project_dir).parent
    indexes_dir = vault_root / "indexes"
    indexes_dir.mkdir(parents=True, exist_ok=True)

    written: list[str] = []
    for tag, slugs in sorted(tag_to_slugs.items()):
        tag_slug = tag.replace("/", "-")
        index_path = indexes_dir / f"{tag_slug}.md"

        if index_path.exists():
            existing = index_path.read_text(encoding="utf-8")
            if _GENERATED_MARKER not in existing:
                continue

        wikilinks = "\n".join(f"- [[{s}]]" for s in sorted(slugs))
        content = (
            f"---\nname: {tag}\ntype: index\ntags:\n- type/index\n---\n"
            f"\n{_GENERATED_MARKER}\n\n# {tag}\n\n"
            f"Skills tagged with `{tag}`:\n\n{wikilinks}\n"
        )
        index_path.write_text(content, encoding="utf-8")
        written.append(tag)

    # Remove orphaned index files for tags that no longer exist.
    active_slugs = {tag.replace("/", "-") for tag in tag_to_slugs}
    for index_file in indexes_dir.iterdir():
        if index_file.suffix != ".md":
            continue
        if index_file.stem in active_slugs:
            continue
        existing = index_file.read_text(encoding="utf-8")
        if _GENERATED_MARKER in existing:
            index_file.unlink()

    return written


# ── Skill compilation ────────────────────────────────────────────

_ESSENTIAL_HEADINGS = frozenset(
    {"context", "core knowledge", "decision criteria"}
)
_PROGRESSIVE_DISCLOSURE_THRESHOLD = 500


def compile_skills(
    project_dir: Path,
    issue: int | None = None,
) -> list[str]:
    """Compile vault skills to ``.claude/skills/`` for Claude Code.

    Reads ``skills_required`` from ``state.md``, loads matching skills
    from the personal vault, and writes each to
    ``.claude/skills/<slug>/SKILL.md`` following the Claude Code skill
    specification.

    When ``issue`` is provided, uses the issue's ``skills_required``
    instead of the project-wide list from ``state.md``.  Falls back to
    ``state.md`` if the issue has no ``skills_required``.

    Removes stale skill directories (skills no longer in
    ``skills_required`` or deleted from vault).

    Args:
        project_dir: Directory containing ``.mantle/``.
        issue: Optional issue number to scope skill compilation.

    Returns:
        List of compiled skill slugs.
    """
    skills_target = project_dir / ".claude" / "skills"
    compiled_slugs: list[str] = []

    skills_filter: tuple[str, ...] = ()
    if issue is not None:
        # Local import to avoid circular dependency:
        # issues -> state <- skills -> issues
        from mantle.core import issues as issues_mod

        issue_path = issues_mod.find_issue_path(project_dir, issue)
        if issue_path is not None:
            note, _ = issues_mod.load_issue(issue_path)
            if note.skills_required:
                skills_filter = note.skills_required

    try:
        matches = _match_required_skills(
            project_dir, skills_filter=skills_filter
        )
    except VaultNotConfiguredError, FileNotFoundError:
        _cleanup_stale_skills(skills_target, compiled_slugs)
        return compiled_slugs

    for name, path in matches:
        if path is None:
            warnings.warn(
                f"Skill '{name}' in skills_required but not found in vault",
                stacklevel=2,
            )
            continue

        note, body = load_skill(path)
        slug = _slugify(note.name)
        content = _extract_content(body)
        trigger_source = note.when_to_use or note.description

        _write_compiled_skill(skills_target, slug, trigger_source, content)
        compiled_slugs.append(slug)

    _cleanup_stale_skills(skills_target, compiled_slugs)
    if compiled_slugs:
        _ensure_skills_gitignore(project_dir)

    try:
        generate_index_notes(project_dir)
    except (VaultNotConfiguredError, FileNotFoundError, OSError) as exc:
        warnings.warn(
            f"Index generation failed: {exc}",
            stacklevel=2,
        )

    return compiled_slugs


def _write_compiled_skill(
    skills_target: Path,
    slug: str,
    description: str,
    content: str,
) -> None:
    """Write a compiled skill to ``.claude/skills/<slug>/``.

    Always produces a folder with progressive disclosure::

        <slug>/
        ├── SKILL.md          # Lean summary + pointers
        └── references/
            └── core.md       # Full skill content

    For long content (>500 lines), SKILL.md contains only essential
    sections; reference sections go into ``references/core.md``.
    For short content, SKILL.md has a summary and pointer;
    ``references/core.md`` holds the full content.

    Args:
        skills_target: Root ``.claude/skills/`` directory.
        slug: Skill slug used as directory name.
        description: Skill description for frontmatter.
        content: Authored content (after ``<!-- mantle:content -->``).
    """
    skill_dir = skills_target / slug
    refs_dir = skill_dir / "references"
    refs_dir.mkdir(parents=True, exist_ok=True)

    # Clean up legacy flat reference.md
    legacy_ref = skill_dir / "reference.md"
    if legacy_ref.exists():
        legacy_ref.unlink()

    frontmatter = _build_compiled_frontmatter(slug, description)
    pointer = (
        "For detailed knowledge, see [references/core.md](references/core.md)\n"
    )

    lines = content.split("\n")
    if len(lines) > _PROGRESSIVE_DISCLOSURE_THRESHOLD:
        essential, reference = _split_content_for_disclosure(content)
        skill_md = (
            frontmatter
            + essential
            + "\n\n## Additional resources\n\n- "
            + pointer
        )
        (refs_dir / "core.md").write_text(reference, encoding="utf-8")
    else:
        skill_md = frontmatter + pointer
        (refs_dir / "core.md").write_text(content, encoding="utf-8")

    (skill_dir / "SKILL.md").write_text(skill_md, encoding="utf-8")


def _to_trigger_description(description: str) -> str:
    """Transform a summary description into a trigger-style description.

    Trigger descriptions tell Claude *when* to activate the skill,
    not *what* it contains. If the description already starts with
    ``TRIGGER``, it is returned unchanged.

    Args:
        description: Original skill description.

    Returns:
        Description prefixed with ``TRIGGER when``.
    """
    if description.upper().startswith("TRIGGER"):
        return description
    if description.lower().startswith("use when "):
        return f"TRIGGER when {description[9:]}"
    return f"TRIGGER when using {description}"


def _build_compiled_frontmatter(slug: str, description: str) -> str:
    """Build YAML frontmatter for a compiled SKILL.md.

    Args:
        slug: Skill slug for the ``name`` field.
        description: Skill description.

    Returns:
        Frontmatter string including ``---`` delimiters.
    """
    data = {
        "name": slug,
        "description": _to_trigger_description(description),
        "user-invocable": False,
    }
    frontmatter = yaml.dump(
        data,
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
    )
    return f"---\n{frontmatter}---\n\n"


def _split_content_for_disclosure(
    content: str,
) -> tuple[str, str]:
    """Split content into essential and reference sections.

    Essential sections: Context, Core Knowledge, Decision Criteria.
    Reference sections: everything else (Examples, Anti-patterns).

    Args:
        content: Full authored content.

    Returns:
        Tuple of (essential content, reference content).
    """
    sections = _parse_content_sections(content)

    essential_parts: list[str] = []
    reference_parts: list[str] = []

    for heading, body in sections:
        if heading.lower().strip() in _ESSENTIAL_HEADINGS:
            essential_parts.append(f"## {heading}\n\n{body}")
        else:
            reference_parts.append(f"## {heading}\n\n{body}")

    if not essential_parts:
        return content, ""

    return "\n\n".join(essential_parts), "\n\n".join(reference_parts)


def _parse_content_sections(
    content: str,
) -> list[tuple[str, str]]:
    """Parse content into ``(heading, body)`` pairs by ``##`` headings.

    Args:
        content: Markdown content.

    Returns:
        List of ``(heading text, section body)`` tuples.
    """
    parts = re.split(r"^## ", content, flags=re.MULTILINE)
    sections: list[tuple[str, str]] = []

    for part in parts[1:]:
        lines = part.split("\n", 1)
        heading = lines[0].strip()
        body = lines[1].strip() if len(lines) > 1 else ""
        sections.append((heading, body))

    return sections


def _cleanup_stale_skills(
    skills_target: Path,
    compiled_slugs: Sequence[str],
) -> None:
    """Remove skill directories not in the compiled set.

    Args:
        skills_target: Root ``.claude/skills/`` directory.
        compiled_slugs: Slugs that were just compiled.
    """
    if not skills_target.is_dir():
        return
    for child in skills_target.iterdir():
        if child.is_dir() and child.name not in compiled_slugs:
            shutil.rmtree(child)


def _ensure_skills_gitignore(project_dir: Path) -> None:
    """Ensure ``.claude/.gitignore`` contains ``skills/`` entry.

    Args:
        project_dir: Directory containing ``.mantle/``.
    """
    gitignore_path = project_dir / ".claude" / ".gitignore"

    if gitignore_path.exists():
        text = gitignore_path.read_text()
        if "skills/" in text.splitlines():
            return
        if not text.endswith("\n"):
            text += "\n"
        text += "skills/\n"
        gitignore_path.write_text(text)
    else:
        gitignore_path.parent.mkdir(parents=True, exist_ok=True)
        gitignore_path.write_text("skills/\n")
