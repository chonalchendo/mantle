---
issue: 35
title: Core scout module — ScoutReport model, save, load, list
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a developer, I want scout reports persisted in .mantle/scouts/ with structured metadata, so that findings are preserved and can inform future planning.

## Depends On

None — independent (foundation module).

## Approach

Follows the established thin-module CRUD pattern used by brainstorm.py, research.py, and learning.py. Creates a Pydantic model for report frontmatter and provides save/load/list functions using vault.write_note/read_note. Includes state.md update after save.

## Implementation

### src/mantle/core/scout.py (new file)

Create a new core module following the brainstorm.py pattern exactly:

**ScoutReport model (Pydantic, frozen=True):**
- date: date
- author: str
- repo_url: str
- repo_name: str
- dimensions: tuple[str, ...] — e.g. ("architecture", "patterns", "testing", "cli-design")
- tags: tuple[str, ...] = ("type/scout",)

**Public functions:**
- save_scout(project_dir, content, *, repo_url, repo_name, dimensions) -> tuple[ScoutReport, Path]
  - Resolves git identity, creates ScoutReport, writes to .mantle/scouts/<date>-<repo-name-slug>.md
  - Uses vault.write_note with sanitize.strip_analysis_blocks
  - Auto-increments filename on same-day collision (same _resolve pattern as brainstorm.py)
  - Updates state.md Current Focus section
- load_scout(path) -> tuple[ScoutReport, str]
  - Reads using vault.read_note(path, ScoutReport)
- list_scouts(project_dir) -> list[Path]
  - Returns sorted glob of .mantle/scouts/*.md

**Private helpers:**
- _slugify(name: str) -> str — same pattern as brainstorm.py._slugify
- _resolve_scout_path(project_dir, repo_name) -> Path — auto-increment pattern
- _update_state_body(project_dir, identity, repo_name) -> None — updates Current Focus

**Imports:**
- from mantle.core import sanitize, state, vault
- pydantic, re, date from stdlib

#### Design decisions

- **Follows brainstorm.py pattern exactly**: This is a thin CRUD module. No orchestration logic — that lives in the prompt.
- **repo_name as slug source**: The repo name (e.g. "fastapi") is slugified for the filename, not the full URL.
- **dimensions as tuple[str, ...]**: Stored in frontmatter so reports are queryable by dimension.

## Tests

### tests/core/test_scout.py (new file)

- **test_save_scout_creates_file**: save_scout writes .mantle/scouts/<date>-<slug>.md with correct frontmatter and body
- **test_save_scout_auto_increments**: saving two reports for same repo on same day creates -2 suffix
- **test_save_scout_updates_state**: state.md Current Focus is updated after save
- **test_load_scout_roundtrip**: save then load returns matching ScoutReport and body
- **test_list_scouts_empty**: returns empty list when no scouts directory
- **test_list_scouts_sorted**: returns paths sorted oldest-first
- **test_slugify_special_chars**: handles special characters and truncates at 40 chars
- **test_save_scout_strips_analysis_blocks**: content is sanitized via strip_analysis_blocks

Fixture: tmp_path with .mantle/state.md pre-created (use existing test fixtures as reference). Mock state.resolve_git_identity to return a fixed email.