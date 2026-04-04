---
issue: 28
title: Add-issue command — create single issues for existing projects
approaches:
- 'Approach A — Prompt-only command: Create add-issue.md as a static Claude Code slash
  command. Reads existing issues, system design, and brainstorm files for context.
  Interactive session captures title, description, acceptance criteria, slices, and
  dependencies. Deduplication check against existing issues. System design impact
  flagging. Saves via existing mantle save-issue CLI. No new Python code — all infrastructure
  exists.'
- 'Approach B — Prompt + core helper module: Same prompt as A, plus new core/issues.py
  helper with detect_duplicates() and check_design_impact() functions. Over-engineering:
  the AI in the prompt can do dedup and impact analysis by reading files directly.'
chosen_approach: Approach A — Prompt-only command
appetite: small batch
open_questions:
- Should add-issue auto-link to a brainstorm file by title matching, or ask the user
  to specify?
author: 110059232+chonalchendo@users.noreply.github.com
created: '2026-04-04'
updated: '2026-04-04'
updated_by: 110059232+chonalchendo@users.noreply.github.com
tags:
- type/shaped
- phase/shaping
---

## Shaping: Add-issue command

### Problem

After initial project setup with /mantle:plan-issues, there is no way to add a single new issue. Users who complete a brainstorm session and get a "proceed" verdict have no command to create the issue — they'd have to manually write the markdown file.

### Chosen Approach: Prompt-only command

Create `claude/commands/mantle/add-issue.md` as a static Claude Code slash command following the pattern established by brainstorm.md, challenge.md, and other prompt-based commands.

#### Strategy

- Single new file: `claude/commands/mantle/add-issue.md`
- No new Python modules — `mantle save-issue` CLI already handles persistence
- Prompt reads `.mantle/issues/`, `.mantle/system-design.md`, and `.mantle/brainstorms/` for context
- Interactive session (3-5 exchanges) captures: title, description, acceptance criteria, slices, dependencies
- Dedup check: prompt reads all existing issue titles/descriptions and flags overlap
- System design impact: prompt compares proposed architecture touches against system-design.md
- Brainstorm reference: prompt checks `.mantle/brainstorms/` for matching files

#### Fits architecture by

- Follows the "prompt orchestrates, AI implements" pattern from system-design.md
- Uses existing `mantle save-issue` CLI — no new core/ or cli/ code needed
- Consistent with brainstorm.md, challenge.md command structure (allowed-tools, step-based, TaskCreate)
- Respects core-never-imports-cli boundary (no code changes needed)

#### Does not

- Does not modify product-design.md (stubborn vision, per issue spec)
- Does not auto-update system-design.md (flags drift, suggests /mantle:revise-system)
- Does not handle batch issue creation (use /mantle:plan-issues for that)
- Does not create new Python modules or CLI subcommands
- Does not auto-shape or auto-plan — recommends next step only

### Code Design

**New file:** `claude/commands/mantle/add-issue.md`

Steps:
1. Check prerequisites (state.md exists, status is planning)
2. Load context (existing issues, system design, brainstorms)
3. Interactive capture (title, description, AC, slices, deps)
4. Deduplication check
5. System design impact check
6. Save via `mantle save-issue`
7. Recommend next step (/mantle:shape-issue)