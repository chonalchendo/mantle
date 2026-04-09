---
issue: 30
title: Auto-generated index notes — compile integration and vault indexes
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a vault user, I want auto-generated index notes so I can browse skills by topic in Obsidian without manual maintenance.

## Depends On

None — independent. Adds a new function and integrates with compile_skills, but does not depend on stories 1 or 2.

## Approach

Add a generate_index_notes() function to skills.py that reads all vault skills, groups them by tag, and writes index notes to the vault. Integrate this into compile_skills() so indexes are regenerated whenever skills are compiled. Uses a generated marker comment to distinguish auto-generated files from manually-created ones, ensuring existing vault notes are never overwritten.

## Implementation

### src/mantle/core/skills.py (modify)

1. **Add `_GENERATED_MARKER` constant** — `"<!-- mantle:generated -->"`. Used to identify auto-generated files.

2. **Add `generate_index_notes(project_dir: Path) -> list[str]`** — new public function:
   - Read all skills via `list_skills(project_dir)`.
   - For each skill, load frontmatter via `load_skill()` (skip unparseable files).
   - Build a dict mapping each non-type tag to a list of skill names: `dict[str, list[str]]`.
   - For each tag, generate an index note at `<vault>/indexes/<tag-slug>.md` where `<tag-slug>` replaces `/` with `-` (e.g., `domain/concurrency` becomes `domain-concurrency.md`).
   - Before writing, check if the file exists and does NOT contain `_GENERATED_MARKER`. If so, skip it (preserve manually-created notes).
   - Index note format:
     ```markdown
     <!-- mantle:generated -->
     ---
     name: <tag>
     type: index
     tags:
     - type/index
     ---

     # <tag>

     Skills tagged with `<tag>`:

     - [[skill-name-1]]
     - [[skill-name-2]]
     ```
   - Create the `indexes/` directory if it doesn't exist.
   - Return list of tag strings that had index notes written.

3. **Modify `compile_skills()`** — after compiling skills and before returning, call `generate_index_notes(project_dir)`. Wrap in a try/except to not fail compilation if index generation fails (log warning).

#### Design decisions

- **Tag slug uses `-` not `/`**: Filesystem-safe. `domain/concurrency` → `domain-concurrency.md`.
- **Generated marker as HTML comment**: Invisible in Obsidian preview, machine-readable for detection.
- **Wikilinks use skill names, not paths**: Obsidian resolves wikilinks by name — `[[python-asyncio]]` links correctly regardless of folder structure.
- **Index generation in compile_skills, not a separate CLI command**: Users don't need to think about it — indexes stay in sync automatically.
- **Warn on failure, don't crash**: Index generation is a nice-to-have. If the vault is misconfigured, skill compilation should still succeed.

## Tests

### tests/core/test_skills.py (modify)

- **test_generate_index_notes_creates_indexes**: Create 3 skills with overlapping tags (2 with `domain/web`, 1 with `domain/data`). Call generate_index_notes(). Assert two index files created in `<vault>/indexes/`. Assert `domain-web.md` contains wikilinks to both web skills. Assert `domain-data.md` contains wikilink to the data skill.
- **test_generate_index_notes_preserves_manual_files**: Create an index file at `indexes/domain-web.md` WITHOUT the generated marker. Create skills with `domain/web` tag. Call generate_index_notes(). Assert the manual file is unchanged.
- **test_generate_index_notes_overwrites_generated_files**: Create an index file WITH the generated marker. Create skills with different tags. Call generate_index_notes(). Assert the file is updated with new content.
- **test_generate_index_notes_includes_generated_marker**: Generate an index. Read the file. Assert it starts with the generated marker comment.
- **test_generate_index_notes_skips_type_tags**: Create a skill with only `type/skill` tag. Call generate_index_notes(). Assert no index file is created for `type-skill.md`.
- **test_compile_skills_calls_generate_indexes**: Integration test — compile_skills() with skills that have tags. Assert index files are generated in the vault.