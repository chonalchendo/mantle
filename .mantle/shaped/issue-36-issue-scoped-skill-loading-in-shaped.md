---
issue: 36
title: Issue-scoped skill loading in build pipeline
approaches:
- Frontmatter filter — add skills_required to issue frontmatter, compile_skills reads
  it when issue is specified, implement.md injects Required reading section
- Dynamic extraction — no new field, extract keywords from issue content at compile
  time and match against vault skills dynamically
chosen_approach: Frontmatter filter
appetite: small batch
open_questions: []
author: 110059232+chonalchendo@users.noreply.github.com
created: '2026-04-07'
updated: '2026-04-07'
updated_by: 110059232+chonalchendo@users.noreply.github.com
tags:
- type/shaped
- phase/shaping
---

## Approach A: Frontmatter filter (chosen)

Add a `skills_required` field to each issue's YAML frontmatter (like `slice` and `blocked_by`). `compile_skills()` gains an optional `issue` parameter — when set, it reads the issue's `skills_required` and compiles only those. The build/implement prompts inject a `## Required reading` section listing those skill names.

### How it works

1. Issue frontmatter gets `skills_required: [cyclopts, software-design-principles]`
2. `_match_required_skills()` accepts an optional filter list, uses it instead of state.md's full list
3. `compile()` and `compile_skills()` gain an `issue: int | None` param
4. `implement.md` Step 4 extends per-story context briefs with `## Required reading: {skill names}`
5. `auto_update_skills()` writes detected skills to issue frontmatter AND state.md

### Tradeoffs

- **Gain**: Simple, explicit, debuggable — you can see exactly which skills an issue uses
- **Give up**: Field needs populating (mitigated by `update-skills --issue` auto-population)

### Rabbit holes

- Schema migration for existing issues — mitigated by defaulting to `()` which falls back to state.md
- `update-skills --issue` currently only writes to state.md — needs to also write to issue frontmatter

### No-gos

- No auto-detection logic changes (that's issue 26)
- No per-story skill scoping
- No migration of existing issues

---

## Approach B: Dynamic extraction (rejected)

No new frontmatter field. `compile_skills()` reads issue/story content at compile time, extracts keywords, and matches against vault skills dynamically.

### Why rejected

Issue 33's learning explicitly flagged overly-aggressive skill matching as a known problem. Building more matching logic on top of a known-flawed heuristic would likely produce false positives (flooding context) or false negatives (missing critical skills) — the exact problems this issue aims to fix. The frontmatter approach is explicit, debuggable, and follows proven patterns in the codebase.

---

## Code Design

### Strategy

Three changes across two modules and two prompts:

1. **`core/issues.py`** — Add `skills_required: tuple[str, ...] = ()` to `IssueNote` frontmatter model. Mirrors existing `blocked_by` and `slice` fields.

2. **`core/skills.py`** — Modify `compile_skills(project_dir, issue: int | None = None)`:
   - When `issue` is provided: load the issue file, read its `skills_required`, compile only those
   - When `issue` is `None`: current behaviour (read all from state.md)
   - Modify `auto_update_skills()` to also write detected skills into issue frontmatter

3. **`core/compiler.py`** — Thread `issue` param through `compile(project_dir, issue=None)` → `compile_skills(project_dir, issue=None)`.

4. **`claude/commands/mantle/implement.md`** — In Step 4 (context brief per story), add `## Required reading` section listing skill names from issue's `skills_required`.

5. **CLI** — `mantle compile` gains `--issue N` (optional). `mantle save-issue` gains `--skills-required` (optional, repeatable).

### Fits architecture by

- `IssueNote` frontmatter extension follows the same pattern as `slice`, `blocked_by`, `verification` — all optional tuple fields with defaults (core/issues.py:20-39).
- `compile_skills()` already reads from a list (skills_required in state.md) — changing which list when issue is active. One new optional param.
- `compiler.compile()` already calls `skills.compile_skills(project_dir)` at line 162 — threading `issue` param is a one-line change.
- `implement.md` Step 4 already builds per-story context briefs. Adding `## Required reading` is additive content.
- All logic stays in `core/`. Follows core-never-imports-cli boundary.

### Does not

- Does not auto-detect skills from issue content — that's issue 26's job. This adds the field and consumes it.
- Does not migrate existing issues — old issues default to `()`, triggering fallback to state.md's full list.
- Does not change `update-skills --issue` detection logic — matching heuristic stays as-is.
- Does not add per-story skill scoping — all stories share the issue's skill set.
- Does not change SessionStart hook — `compile_if_stale` continues to compile all skills (no issue context at session start).