---
issue: 21
title: Compile vault skills to .claude/skills/ for native loading
status: completed
failure_log: null
tags:
  - type/story
  - status/pending
---

## Implementation

### `src/mantle/core/skills.py`

Add a `compile_skills()` function that syncs relevant vault skills into Claude Code's native skill directory format.

```python
def compile_skills(project_dir: Path) -> list[str]:
    """Compile vault skills to .claude/skills/ for Claude Code native loading.

    Reads skills_required from state.md, loads matching skills from the
    personal vault, and writes each to .claude/skills/<slug>/SKILL.md
    following the Claude Code skill specification.

    Removes stale skill directories (skills no longer in skills_required
    or deleted from vault).

    Returns list of compiled skill names.
    """
```

### Claude Code skill format

Claude Code discovers skills from `.claude/skills/<skill-name>/SKILL.md` (project-level) or `~/.claude/skills/<skill-name>/SKILL.md` (user-level). Each skill is a directory with `SKILL.md` as the entrypoint plus optional supporting files.

The compiled directory structure per skill:

```
.claude/skills/<skill-slug>/
├── SKILL.md           # Main instructions (required)
└── reference.md       # Detailed content if SKILL.md exceeds 500 lines (optional)
```

`SKILL.md` uses YAML frontmatter for discovery and control:

```yaml
---
name: python-asyncio
description: "Async Python patterns using asyncio. Use when building concurrent I/O-bound services or writing async code."
user-invocable: false
---

## Context

Async Python patterns using asyncio for concurrent I/O-bound services.

## Core Knowledge

Use `asyncio.TaskGroup` for structured concurrency instead of `gather()`.

## Decision Criteria

Use asyncio for I/O-bound concurrency. Use multiprocessing for CPU-bound work.

## Anti-patterns

- Use `TaskGroup` instead of `gather()` for structured concurrency.
```

### Frontmatter mapping

Map vault skill metadata to Claude Code's SKILL.md frontmatter:

| Vault field (SkillNote) | SKILL.md frontmatter | Notes |
|---|---|---|
| `name` (slugified) | `name` | Lowercase, hyphens. Max 64 chars. |
| `description` | `description` | The most important field — Claude uses this to decide when to load the skill. Must describe what the skill covers AND when it's relevant. |
| — | `user-invocable: false` | Always set. Vault skills are background knowledge for Claude, not user-invocable slash commands. |

Fields NOT mapped: `proficiency`, `related_skills`, `projects`, `last_used`, `author`, `tags` — these are vault metadata for Obsidian, not relevant to Claude Code's skill loading.

### Content mapping

The body of SKILL.md is the authored content from the vault — everything after the `<!-- mantle:content -->` marker. The wikilink sections (Related Skills, Projects) are omitted since they're Obsidian-specific and not useful to Claude.

### Progressive disclosure

Claude Code recommends keeping SKILL.md under 500 lines. If a vault skill's authored content exceeds 500 lines:

1. Write the Context, Core Knowledge, and Decision Criteria sections to `SKILL.md` (the essentials)
2. Write Examples and Anti-patterns to `reference.md`
3. Add a reference link at the bottom of `SKILL.md`:

```markdown
## Additional resources

- For examples and anti-patterns, see [reference.md](reference.md)
```

Claude loads `SKILL.md` when the skill is activated and reads `reference.md` on demand via the file reference.

### Description quality

The `description` field drives Claude Code's skill discovery — it determines whether a skill gets loaded into context. During compilation, use the vault skill's `description` field directly. The add-skill workflow (story authoring) already coaches the user to write descriptions that include both what the skill covers and when it's relevant (per the existing skill effectiveness research).

Context budget: Claude Code loads skill descriptions at 2% of the context window (~16,000 chars). Each description should be under 200 chars to leave room for other skills.

### Compilation logic

1. Read `skills_required` from `state.md`
2. For each required skill, find the matching vault file using `_match_skill_slug()`
3. Load the skill via `load_skill()`
4. Build the SKILL.md frontmatter (`name`, `description`, `user-invocable: false`)
5. Extract authored content (after `<!-- mantle:content -->` marker)
6. If content exceeds 500 lines, split into SKILL.md + reference.md
7. Write to `.claude/skills/<slug>/SKILL.md` (and `reference.md` if split)
8. After writing all required skills, scan `.claude/skills/` for directories not in the current required set — delete them (stale cleanup)

### `src/mantle/core/compiler.py`

Update `compile()` to call `skills.compile_skills(project_dir)` after compiling commands. This integrates skill compilation into the existing `mantle compile` / `mantle compile --if-stale` flow.

### Staleness detection

Add skill vault files to the existing manifest hash tracking in `compiler.py`. When a skill file in the vault changes, the manifest detects staleness and triggers recompilation.

### `.claude/.gitignore`

Add `skills/` to `.claude/.gitignore` — compiled skills are derived artifacts, not source. Each developer's skill set may differ.

### `claude/commands/mantle/add-skill.md`

After Step 6 (save skill), trigger recompilation so the new skill is immediately available to Claude Code:

```
Run: mantle compile --force
```

### Design decisions

- **Compile to project-level `.claude/skills/`.** Claude Code discovers skills from `.claude/skills/` (project) or `~/.claude/skills/` (personal). Project-level is correct because skills are filtered by `skills_required` per project — different projects get different skills.
- **Set `user-invocable: false` on all compiled skills.** Vault skills are reference knowledge (conventions, patterns, domain knowledge) — not task-oriented commands. Claude should load them automatically when relevant, but they shouldn't appear in the `/` menu. Users invoke skills via `/mantle:add-skill`, not via the compiled skill directly.
- **Only compile `skills_required` skills.** Don't dump all vault skills into every project. The project's `state.md` already declares which skills are relevant. This also respects Claude Code's context budget for skill descriptions.
- **Omit vault-specific metadata.** `proficiency`, `related_skills`, `projects`, `tags`, and wikilink sections are for Obsidian's graph — Claude Code doesn't need them. Only `name`, `description`, and authored content are compiled.
- **Split at 500 lines.** Claude Code recommends keeping SKILL.md under 500 lines. Large skills get a `reference.md` that Claude reads on demand, following the progressive disclosure pattern.
- **Stale cleanup on every compile.** If a skill is removed from `skills_required` or deleted from the vault, its `.claude/skills/` directory is removed. Prevents ghost skills from lingering in Claude's context budget.
- **Compiled skills are gitignored.** Skills are personal vault content, not project source. Each collaborator's compiled skills differ based on their vault.
- **Recompile after add-skill.** The new skill is immediately available without waiting for the next session start.

## Tests

### tests/core/test_skills.py

- **test_compile_skills_creates_directories**: Compiling with two required skills creates `.claude/skills/<slug>/SKILL.md` for each
- **test_compile_skills_frontmatter**: Compiled SKILL.md has `name`, `description`, and `user-invocable: false` in frontmatter
- **test_compile_skills_content_excludes_wikilinks**: Compiled body contains authored content but not Related Skills / Projects wikilink sections
- **test_compile_skills_progressive_disclosure**: Skill with >500 lines of content produces SKILL.md + reference.md with cross-reference link
- **test_compile_skills_short_content_no_split**: Skill under 500 lines produces only SKILL.md, no reference.md
- **test_compile_skills_stale_cleanup**: Skill removed from `skills_required` → its `.claude/skills/` directory is deleted
- **test_compile_skills_missing_vault_skill**: Skill in `skills_required` but not in vault → skipped with warning (not an error)
- **test_compile_skills_no_skills_required**: Empty `skills_required` → `.claude/skills/` is empty, any existing dirs cleaned up
- **test_compile_skills_idempotent**: Running compile twice with same inputs produces identical output
- **test_compile_skills_description_preserved**: The vault skill's `description` field is used verbatim in compiled frontmatter

### tests/core/test_compiler.py

- **test_compile_includes_skills**: Full `compile()` call also compiles skills (integration test)
- **test_compile_staleness_detects_skill_changes**: Changing a vault skill file triggers recompilation
