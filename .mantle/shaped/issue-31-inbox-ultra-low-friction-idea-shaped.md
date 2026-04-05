---
issue: 31
title: Inbox — ultra-low-friction idea capture for project feature ideas
approaches:
- 'Bug-Pattern Lite: Follow bugs.py pattern — InboxItem model, save/list/update_status,
  cli wrapper. Small batch.'
- 'Flat List in state.md: Store inbox items as YAML list in state.md. Zero new files
  but doesn''t scale.'
- 'Full Inbox Manager: Add search, tagging, bulk operations. Over-engineered for a
  parking lot feature.'
chosen_approach: Bug-Pattern Lite
appetite: small batch
open_questions:
- Should dismissed items be deleted or kept with status=dismissed?
author: 110059232+chonalchendo@users.noreply.github.com
created: '2026-04-05'
updated: '2026-04-05'
updated_by: 110059232+chonalchendo@users.noreply.github.com
tags:
- type/shaped
- phase/shaping
---

## Rationale

Bug-Pattern Lite is the clear winner. The inbox is structurally identical to bugs — dated markdown files with YAML frontmatter and status tracking. The only difference is simpler content (title + optional description vs. reproduction steps). All 6 ACs map directly to this pattern.

## Code Design

### Strategy

New `core/inbox.py` module with:
- `InboxItem` pydantic model (title, description, source, status, date, author, tags)
- `save_inbox_item(project_dir, title, description, source)` → (InboxItem, Path)
- `list_inbox_items(project_dir, status=None)` → list[Path]
- `load_inbox_item(path)` → (InboxItem, str)
- `update_inbox_status(project_dir, filename, status)` → (InboxItem, str)

New `cli/inbox.py` with thin `run_save_inbox_item()` and `run_update_inbox_status()` wrappers.

CLI command: `mantle save-inbox-item --title '...' [--description '...'] [--source user|ai]`
CLI command: `mantle update-inbox-status --item '...' --status promoted|dismissed`

Add `inbox` to SUBDIRS in `core/project.py`.

Static prompt: `claude/commands/mantle/inbox.md` — asks for title + optional description, saves via CLI.

### Fits architecture by

- core/inbox.py follows same pattern as core/bugs.py (pydantic model, vault.write_note, vault.read_note)
- cli/inbox.py follows cli/bugs.py (thin wrapper, rich console output, SystemExit on errors)
- core/ never imports from cli/ — maintained
- SUBDIRS addition follows core/project.py pattern for mantle init
- Plan-issues integration: plan-issues.md prompt reads .mantle/inbox/ and surfaces open items (prompt-level, not code)
- Build pipeline integration: build.md Step 9 summary mentions AI-captured ideas (prompt-level)

### Does not

- Does not add search, filtering, or bulk operations (not in ACs)
- Does not validate user input beyond source enum (CLI layer responsibility)
- Does not modify plan-issues.md or build.md prompts (separate prompt changes, tested manually)
- Does not implement AI auto-suggestion logic (that's in the prompt, not the runtime)
- Does not persist state.md changes (inbox is fire-and-forget, not a state transition)