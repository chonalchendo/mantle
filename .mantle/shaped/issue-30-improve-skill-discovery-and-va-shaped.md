---
issue: 30
title: Improve skill discovery and vault navigation
approaches:
- Extend in place — tag filtering, detection, and index generation all in existing
  modules (skills.py, compiler.py, main.py)
- Index module — new core/indexes.py for index note generation, other changes in existing
  modules
chosen_approach: Extend in place
appetite: small batch
open_questions:
- Should description matching use word overlap or substring? Word overlap is safer
  but might miss relevant skills.
author: 110059232+chonalchendo@users.noreply.github.com
created: '2026-04-05'
updated: '2026-04-05'
updated_by: 110059232+chonalchendo@users.noreply.github.com
tags:
- type/shaped
- phase/shaping
---

## Approaches

### Approach A: Extend in place (chosen)

Add tag filtering to list_skills(), extend detect_skills_from_content() to match on tags and description, and add index note generation to compile_skills(). All changes in existing modules — no new files.

- **Appetite**: Small batch (1-2 days)
- **Tradeoffs**: Keeps skills.py as the single module for all skill operations. Index generation is a natural extension of compilation.
- **Rabbit holes**: Tag matching on content could produce false positives if description text is too generic. Mitigate by requiring tag prefix match (e.g., only match "domain/concurrency" tags, not bare words from descriptions).
- **No-gos**: No semantic/AI matching — purely tag and string-based.

### Approach B: Index module

Create core/indexes.py for index note generation. Tag filtering and detection stay in skills.py.

- **Appetite**: Small batch (1-2 days)
- **Tradeoffs**: Cleaner separation but adds a thin module for ~50 lines of code. Premature abstraction.
- **Why not**: The index generation logic is tightly coupled to skill metadata and vault paths — it belongs in skills.py alongside compile_skills().

## Rationale

Approach A follows the project's "deep modules" philosophy. skills.py already handles skill CRUD, detection, compilation, and gap analysis. Adding tag filtering and index generation keeps the interface simple (three more parameters/functions) while hiding complexity. Creating a new module for ~50 lines violates the "three similar lines is better than a premature abstraction" principle.

## Code Design

### Strategy

**core/skills.py** — three changes:

1. `list_skills(project_dir, *, tag: str | None = None) -> list[Path]` — add optional `tag` kwarg. When provided, read each skill's frontmatter and filter to those whose `tags` tuple contains the given tag. Return filtered paths.

2. `detect_skills_from_content(project_dir, content)` — extend the matching loop to also check:
   - Whether any of the skill's `tags` (minus `type/skill`) appear as substrings in the content
   - Whether the skill's `description` has significant word overlap with the content (3+ word tokens in common, excluding stopwords)

3. `generate_index_notes(project_dir) -> list[str]` — new function called during compilation. Reads all skills, groups by tag prefix (`topic/`, `domain/`), writes an index note per tag to `<vault>/indexes/<tag-slug>.md` with wikilinks to each matching skill. Returns list of generated index paths. Skips tags where an existing non-generated file exists (checks for `<!-- mantle:generated -->` marker).

**cli/main.py** — one change:

4. `list_skills_command()` — add `--tag` parameter that passes through to `skills.list_skills()`.

**core/compiler.py** — one change:

5. In `compile()` or wherever `compile_skills()` is called — also call `generate_index_notes()` after skill compilation.

### Fits architecture by

- `core/skills.py` is already the module for "CRUD on skill nodes, gap detection, skill loading for context" per system-design.md. Tag filtering and index generation are natural extensions.
- `cli/main.py` remains a thin routing layer — adds one parameter to one command.
- Index notes are written to the personal vault (`~/vault/indexes/`), consistent with skills living in `~/vault/skills/`.
- `compile_skills()` already runs during SessionStart hook — index generation piggybacks on the same trigger.

### Does not

- Does not add semantic/AI matching — purely string and tag-based filtering.
- Does not modify the build pipeline (Step 3) — backwards compatible by design.
- Does not create a new core module — all logic stays in skills.py.
- Does not overwrite manually-created vault notes — uses a generated marker to distinguish.
- Does not change the skill frontmatter schema — uses existing `tags` field.