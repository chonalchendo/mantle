---
issue: 7
title: Core system design update function with decision logging
status: completed
failure_log: null
tags:
  - type/story
  - status/completed
---

## Implementation

Add `update_system_design()` to `core/system_design.py` that overwrites the existing system design document with revised content and auto-creates a decision log entry. Mirrors the product design revision pattern from story 01 but works with freeform body content rather than structured fields.

### src/mantle/core/system_design.py (modify)

#### New function

- `update_system_design(project_dir, content, *, change_topic, change_summary, change_rationale) -> tuple[SystemDesignNote, Path]` — Load current system design (raise `FileNotFoundError` if missing). Overwrite `.mantle/system-design.md` with the new content body. Preserve original `author` and `created` from existing note. Stamp `updated`/`updated_by` with current git identity and today's date. Call `decisions.save_decision()` to create a decision log entry. Return the updated note and the decision log entry path.

#### Decision log entry construction

The decision log entry is created by calling `decisions.save_decision()` with:
- `topic`: `change_topic` (caller provides, e.g. "revise-architecture-layers")
- `decision`: `change_summary` (what changed)
- `alternatives`: `["Keep current design"]`
- `rationale`: `change_rationale` (why it changed)
- `reversal_trigger`: `"Revert if change no longer serves system goals."`
- `confidence`: `"7/10"`
- `reversible`: `"high"`
- `scope`: `"system-design"`

#### Import change

Add `from mantle.core import decisions` alongside existing `state` and `vault` imports.

#### Design decisions

- **Freeform content, not structured fields**: System design is a long-form markdown document, not structured frontmatter fields like product design. The entire body is replaced.
- **Same timestamp/author preservation pattern as product design revision**: `author`/`created` preserved, `updated`/`updated_by` refreshed.
- **No state transition**: Same reasoning as product design — revisions can happen at any phase.
- **`content` is positional**: Matches existing `save_system_design(project_dir, content, ...)` API shape for consistency.

## Tests

Test fixture creates `.mantle/` with `state.md` at `Status.SYSTEM_DESIGN` and an existing `system-design.md` (via `save_system_design` from a `Status.PRODUCT_DESIGN` state, then the fixture overrides state to `SYSTEM_DESIGN`).

- **update_system_design**: updated note body contains revised content
- **update_system_design**: preserves original `author` and `created`
- **update_system_design**: stamps `updated`/`updated_by` with git identity
- **update_system_design**: round-trip with `load_system_design` returns updated content
- **update_system_design**: creates decision log entry in `.mantle/decisions/`
- **update_system_design**: decision entry has correct topic, scope "system-design"
- **update_system_design**: decision entry body contains change summary and rationale
- **update_system_design**: raises `FileNotFoundError` when system-design.md missing
- **update_system_design**: does not change project state status
- **update_system_design**: second revision creates a second decision log entry
