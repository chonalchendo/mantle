---
issue: 27
title: Core brainstorm module — BrainstormNote, save, load, list
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a developer mid-project, I want brainstorm sessions persisted to `.mantle/brainstorms/` so that validated ideas and scrapped ideas are both preserved as structured context for future planning.

## Depends On

None — independent (new module, no dependencies on other stories).

## Approach

Follow the exact pattern of `core/challenge.py` and `core/research.py` — a Pydantic frozen model for frontmatter, a save function with auto-increment filenames, load/list/exists helpers, and a state.md update. The key difference: brainstorm doesn't depend on `idea.md` (it's for existing projects), and it includes a `verdict` field in frontmatter (proceed/research/scrap).

## Implementation

### src/mantle/core/brainstorm.py (new file)

Module docstring: `"""Brainstorm sessions — validate feature ideas against existing vision."""`

**Constants:**
- `VALID_VERDICTS: frozenset[str]` = `{"proceed", "research", "scrap"}`

**Data model:**
- `BrainstormNote(pydantic.BaseModel, frozen=True)`:
  - `date: date`
  - `author: str`
  - `title: str` (short slug for the idea being brainstormed)
  - `verdict: str` (one of VALID_VERDICTS)
  - `tags: tuple[str, ...] = ("type/brainstorm",)`

**Public API:**
- `save_brainstorm(project_dir: Path, content: str, *, title: str, verdict: str) -> tuple[BrainstormNote, Path]`:
  - Validates verdict against VALID_VERDICTS (raise ValueError if invalid)
  - Resolves git identity via `state.resolve_git_identity()`
  - Creates `BrainstormNote` with today's date, identity, title, verdict
  - Writes to `.mantle/brainstorms/YYYY-MM-DD-<slug>.md` via `vault.write_note()`
  - Strips analysis blocks via `sanitize.strip_analysis_blocks(content)`
  - Calls `_update_state_body()` to update state.md Current Focus
  - Returns `(note, path)`

- `load_brainstorm(path: Path) -> tuple[BrainstormNote, str]`:
  - Reads via `vault.read_note(path, BrainstormNote)`
  - Returns `(note.frontmatter, note.body)`

- `list_brainstorms(project_dir: Path) -> list[Path]`:
  - Globs `.mantle/brainstorms/*.md`, returns sorted oldest-first
  - Returns empty list if directory doesn't exist

- `brainstorm_exists(project_dir: Path) -> bool`:
  - Returns `len(list_brainstorms(project_dir)) > 0`

**Internal helpers:**
- `_slugify(title: str) -> str`:
  - Lowercase, replace non-alphanumeric with hyphens, strip leading/trailing hyphens, truncate to 40 chars
  - Example: "MotherDuck Interactive Queries" -> "motherduck-interactive-queries"

- `_resolve_brainstorm_path(project_dir: Path, title: str) -> Path`:
  - Computes `brainstorms_dir / f"{today}-{slug}.md"`
  - Auto-increments with `-2`, `-3` suffix on collision (same pattern as `challenge.py:_resolve_challenge_path`)

- `_update_state_body(project_dir: Path, identity: str, verdict: str) -> None`:
  - Reads state.md via `vault.read_note()`
  - Replaces Current Focus section with verdict-appropriate message:
    - proceed: "Brainstorm completed (proceed) — run /mantle:add-issue next."
    - research: "Brainstorm completed (research needed) — run /mantle:research next."
    - scrap: "Brainstorm completed (scrapped) — idea did not align with vision."
  - Updates `updated` and `updated_by` fields

#### Design decisions

- **No idea.md dependency**: Unlike challenge/research, brainstorm operates on existing projects that may not have an `idea.md`. The `title` param replaces the `idea_ref`/`problem_ref` snapshot used by those modules.
- **Slug from title in filename**: Uses slugified title for human-readable filenames. Pattern: `2026-04-04-motherduck-interactive-queries.md`. Follows research.py's `_resolve_research_path` pattern but uses title slug instead of focus keyword.
- **Verdict in frontmatter**: Enables future filtering (e.g., list all scrapped ideas). Validated against `VALID_VERDICTS` like research.py validates against `VALID_FOCUSES`.

## Tests

### tests/core/test_brainstorm.py (new file)

Fixture: `project(tmp_path)` creates `.mantle/` with `state.md` (status=planning) and `.mantle/brainstorms/` directory. Mock `resolve_git_identity` returning `"test@example.com"`.

- **test_save_brainstorm_creates_file**: save with valid inputs, verify file exists in `.mantle/brainstorms/` and filename matches `YYYY-MM-DD-<slug>.md`
- **test_save_brainstorm_frontmatter**: round-trip save then load, verify all frontmatter fields (date, author, title, verdict, tags)
- **test_save_brainstorm_strips_analysis**: save content containing `<analysis>...</analysis>` blocks, verify they are removed from persisted body
- **test_save_brainstorm_auto_increments**: save twice on same day with same title, verify second file has `-2` suffix
- **test_save_brainstorm_invalid_verdict**: call with verdict="maybe", assert raises ValueError with descriptive message
- **test_load_brainstorm**: save then load via returned path, verify body content matches (minus analysis blocks)
- **test_list_brainstorms_empty**: call on project with no brainstorms directory, returns empty list
- **test_list_brainstorms_sorted**: create three brainstorm files with different dates, verify oldest-first ordering
- **test_brainstorm_exists_true**: save a brainstorm, then assert `brainstorm_exists()` returns True
- **test_brainstorm_exists_false**: assert `brainstorm_exists()` returns False on empty project
- **test_save_brainstorm_updates_state**: save with verdict="proceed", read state.md body, verify Current Focus contains "run /mantle:add-issue next"