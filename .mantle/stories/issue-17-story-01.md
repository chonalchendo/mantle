---
issue: 17
title: Core skills module — create, load, list, update, exists
status: completed
failure_log: null
tags:
  - type/story
  - status/completed
---

## Implementation

Build the core skills module for CRUD operations on skill nodes in the personal vault. Each skill node is a knowledge artifact — metadata (description, proficiency, connections) plus authored content written for Claude's consumption (patterns, decision criteria, examples, gotchas). Skill nodes live in `~/vault/skills/<skill-name>.md` (path from `.mantle/config.md` `personal_vault` field). Follows `core/idea.py` and `core/challenge.py` patterns. Key difference: writes to the personal vault (not `.mantle/`), so uses `project.read_config()` to resolve the vault path.

### Research context

Research (`.mantle/research/2026-03-02-skill-effectiveness.md`) found that Claude Code skills use a three-tier loading model. The `description` field is the single most important metadata — it determines whether a skill gets activated. Content should be dense, imperative, written for Claude (not as a human tutorial), and ideally 50–150 lines. Every token must earn its place.

### src/mantle/core/skills.py

```python
"""Skill graph — knowledge nodes with metadata in the personal vault."""
```

#### Data model

```python
class SkillNote(pydantic.BaseModel, frozen=True):
    name: str
    description: str           # what this skill covers + when it's relevant
    type: str = "skill"
    proficiency: str           # "N/10" format
    related_skills: tuple[str, ...] = ()   # wikilink targets
    projects: tuple[str, ...] = ()         # wikilink targets
    last_used: date
    author: str
    created: date
    updated: date
    updated_by: str
    tags: tuple[str, ...] = ("type/skill",)
```

`description` is the one-line summary of what the skill covers and when it's relevant. Research shows this is the most important field for skill activation and matching — analogous to the `description` field in Claude Code SKILL.md files. Written in third person: "Async Python patterns using asyncio. Use when building concurrent I/O-bound services."

`related_skills` and `projects` store plain names; the body builder renders them as `[[wikilinks]]` in the header section before the authored content.

#### Exceptions

```python
class VaultNotConfiguredError(Exception):
    """Raised when personal_vault is not set in config."""

class SkillExistsError(Exception):
    path: Path
```

`VaultNotConfiguredError` raised when `project.read_config()` has no `personal_vault` key or it's `None`. `SkillExistsError` raised when the skill file already exists and `overwrite=False`.

#### Functions

- `create_skill(project_dir, *, name, description, proficiency, content, related_skills=(), projects=(), overwrite=False) -> tuple[SkillNote, Path]` — Validate proficiency against `"N/10"` format. Resolve personal vault path via `project.read_config(project_dir)["personal_vault"]`. Slugify name for filename (`name.lower().replace(" ", "-")`). Write to `<vault>/skills/<slug>.md` with frontmatter and body. The body combines a wikilink header (related skills, projects) with the authored `content`. Raise `VaultNotConfiguredError` if vault not configured. Raise `SkillExistsError` if exists and not overwriting. Returns the note and the written path.

- `load_skill(path) -> tuple[SkillNote, str]` — Read a skill file by absolute path via `vault.read_note()`. Returns `(frontmatter, body)` tuple so callers get both metadata and content. Composable with `list_skills()`.

- `list_skills(project_dir) -> list[Path]` — All skill paths in `<vault>/skills/`, sorted alphabetically. Empty list if none or if directory doesn't exist. Raises `VaultNotConfiguredError` if vault not configured.

- `skill_exists(project_dir, name) -> bool` — Check whether `<vault>/skills/<slug>.md` exists. Raises `VaultNotConfiguredError` if vault not configured.

- `update_skill(project_dir, name, *, description=None, proficiency=None, content=None, related_skills=None, projects=None) -> SkillNote` — Update fields on an existing skill. If `content` is provided, replaces the content section in the body while preserving the wikilink header. Refreshes `updated`/`updated_by`/`last_used` timestamps. Raises `FileNotFoundError` if skill doesn't exist.

#### Internal helpers

- `_resolve_vault_skills_dir(project_dir) -> Path` — Read `personal_vault` from config, expand/resolve, return `<vault>/skills/`. Raise `VaultNotConfiguredError` if not configured.

- `_slugify(name) -> str` — `name.lower().replace(" ", "-")`. Keeps it simple — alphanumeric and hyphens only.

- `_validate_proficiency(proficiency) -> None` — Check `"N/10"` format where N is 1-10. Raise `ValueError` on invalid.

- `_build_skill_body(note, content) -> str` — Build the full markdown body. Structure:
  1. `## Related Skills` — bulleted `[[wikilinks]]` (omitted if empty)
  2. `## Projects` — bulleted `[[wikilinks]]` (omitted if empty)
  3. The authored content, inserted as-is (already markdown with its own headings)

  The content is the substance of the node. It should be written in imperative form, for Claude's consumption — dense, opinionated, actionable. The `/mantle:add-skill` command coaches the user through authoring content that follows the recommended structure from research: context → core knowledge → examples → decision criteria → anti-patterns.

  The `_build_skill_body` function does NOT impose content structure — it just prepends the wikilink sections and includes the authored content verbatim. Content structure is the Claude command's job.

#### Imports

```python
from mantle.core import project, state, vault
```

#### Design decisions

- **`description` is required and prominent**. Research shows this is the single most important field for skill activation. It determines whether a skill gets loaded when matching against `skills_required`. Written in third person, includes both what and when.
- **Content is required on create**. `create_skill()` takes a mandatory `content` parameter. A skill node without content is just a tag — the whole point is capturing knowledge that's useful when loaded into Claude's context during implementation.
- **Content is authored markdown, not structured by the core module**. The `_build_skill_body` function inserts content verbatim. The recommended structure (context → knowledge → examples → decision criteria → anti-patterns) is enforced by the Claude command in story 04, not by the core module. This keeps the core flexible — different skills need different structures.
- **Personal vault, not `.mantle/`**. Skills are cross-project. The vault path comes from `project.read_config()`. This is the first core module that writes outside `.mantle/`.
- **Slugified filenames**. `"Python asyncio"` → `python-asyncio.md`. Simple, URL-safe, grep-friendly.
- **Wikilinks in body header, plain names in frontmatter**. Frontmatter stores `("Python", "FastAPI")`, body renders as `- [[Python]]`. This keeps frontmatter machine-readable while body is Obsidian-native.
- **`load_skill` returns `(frontmatter, body)`**. Unlike `load_idea` which only returns frontmatter, skill loading always needs the body — the content is the whole point. Follows the `load_research` / `load_session` pattern.
- **No state transition**. Skills are ambient knowledge, not workflow steps. Like session logs, they don't change project status.
- **Returns `tuple[SkillNote, Path]` from create**. Caller needs the path for confirmation messages since vault path is user-configured.

## Tests

### tests/core/test_skills.py

All tests use `tmp_path` fixture. Create a `.mantle/` with `config.md` containing `personal_vault: <tmp_path>/vault`. Create `<tmp_path>/vault/skills/` directory. Mock `state.resolve_git_identity()` to return a fixed email.

- **create_skill**: correct frontmatter fields (name, description, type, proficiency, related_skills, projects, last_used, author, created, updated, updated_by, tags)
- **create_skill**: file created at `<vault>/skills/<slug>.md`
- **create_skill**: round-trip with `load_skill` preserves all frontmatter fields
- **create_skill**: round-trip preserves content in body
- **create_skill**: body has `## Related Skills` with wikilinks when related_skills provided
- **create_skill**: body has `## Projects` with wikilinks when projects provided
- **create_skill**: body omits `## Related Skills` when empty
- **create_skill**: body omits `## Projects` when empty
- **create_skill**: body contains authored content verbatim
- **create_skill**: raises `SkillExistsError` when file exists and not overwriting
- **create_skill**: `overwrite=True` replaces existing
- **create_skill**: stamps `author`/`updated_by` with git identity
- **create_skill**: default tags are `("type/skill",)`
- **create_skill**: raises `VaultNotConfiguredError` when vault not configured
- **create_skill**: raises `ValueError` on invalid proficiency format
- **create_skill**: slugifies name with spaces to hyphens
- **create_skill**: slugifies name to lowercase
- **load_skill**: reads saved skill frontmatter correctly (including description)
- **load_skill**: reads saved skill body content
- **load_skill**: raises `FileNotFoundError` when missing
- **list_skills**: returns empty list when no skills
- **list_skills**: returns sorted paths after multiple creates
- **list_skills**: raises `VaultNotConfiguredError` when vault not configured
- **skill_exists**: returns False before creation, True after
- **skill_exists**: raises `VaultNotConfiguredError` when vault not configured
- **update_skill**: updates description
- **update_skill**: updates proficiency
- **update_skill**: updates content in body
- **update_skill**: updates related_skills
- **update_skill**: updates projects
- **update_skill**: refreshes updated/updated_by timestamps
- **update_skill**: refreshes last_used to today
- **update_skill**: preserves unchanged fields
- **update_skill**: preserves content when content not provided
- **update_skill**: raises `FileNotFoundError` when skill doesn't exist
- **SkillNote**: frozen (cannot assign to attributes)
