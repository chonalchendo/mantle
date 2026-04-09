---
issue: 44
title: Sweep prompts batch 2 (design-product, design-system, distill, fix, idea, implement,
  plan-issues)
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a Mantle user running prompts in global storage mode, I want `/mantle:design-product`, `/mantle:design-system`, `/mantle:distill`, `/mantle:fix`, `/mantle:idea`, `/mantle:implement`, and `/mantle:plan-issues` to find the right `.mantle/` directory automatically so the workflow does not silently break.

## Depends On

Story 1 (the `mantle where` CLI command must exist before prompts can call it).

May run in parallel with Story 2, Story 4 (independent file sets).

## Approach

Mechanical sweep of 7 Claude Code prompt files using the same universal pattern as Story 2. Each file gets the `MANTLE_DIR=$(mantle where)` prelude inserted at the top of Step 1, then every literal `.mantle/...` Read-tool target is replaced with `$MANTLE_DIR/...`.

## Implementation

### Universal pattern (identical to Story 2)

At the top of Step 1, insert the resolve-path prelude:

```markdown
First, resolve the project's .mantle/ directory:

    MANTLE_DIR=$(mantle where)

All subsequent `Read` and `Grep`/`Glob` calls in this prompt must use
`$MANTLE_DIR/...` in place of `.mantle/...`.
```

Then mechanically substitute `.mantle/` → `$MANTLE_DIR/` everywhere it appears as a Read/Grep/Glob target. Leave help text, descriptions, and `mantle save-*` flag values alone (those go to the CLI which already resolves paths internally).

### claude/commands/mantle/design-product.md (modify)

Sweep all `.mantle/state.md`, `.mantle/idea.md`, `.mantle/product-design.md`, `.mantle/challenges/`, `.mantle/research/` Read targets.

### claude/commands/mantle/design-system.md (modify)

Sweep all `.mantle/state.md`, `.mantle/product-design.md`, `.mantle/system-design.md`, `.mantle/research/` Read targets.

### claude/commands/mantle/distill.md (modify)

Sweep the vault-search list at Step 3 — every entry like `.mantle/learnings/`, `.mantle/decisions.md`, `.mantle/sessions/`, `.mantle/brainstorms/`, `.mantle/research/`, `.mantle/shaped/` becomes `$MANTLE_DIR/...`. The `mantle save-distillation` and `mantle list-distillations` invocations are unchanged.

### claude/commands/mantle/fix.md (modify)

Sweep all `.mantle/state.md`, `.mantle/issues/`, `.mantle/reviews/` Read targets.

### claude/commands/mantle/idea.md (modify)

Sweep all `.mantle/state.md` and `.mantle/idea.md` Read targets. Note: this prompt has `.mantle/idea.md` mentioned in its description and in Step 1 ("whether `.mantle/idea.md` already exists by reading the file") — only the actual Read tool call in Step 1 needs updating; the description mention is left alone.

### claude/commands/mantle/implement.md (modify)

Sweep all `.mantle/state.md`, `.mantle/issues/`, `.mantle/stories/`, `.mantle/shaped/`, `.mantle/learnings/` Read targets.

### claude/commands/mantle/plan-issues.md (modify)

Sweep all `.mantle/state.md`, `.mantle/product-design.md`, `.mantle/system-design.md`, `.mantle/issues/` Read targets.

#### Design decisions

- **Same prelude as Story 2**: Identical wording so future grep migrations are trivial. If Story 2 changed the wording, this story must match.
- **Vault-search lists are in scope**: `distill.md` and `query.md` (Story 4) have bullet lists describing where to search — those lists describe Read/Glob targets, so they get `$MANTLE_DIR` substitution.
- **Description-only mentions are out of scope**: `idea.md` mentions `.mantle/idea.md` in its top-of-file description text — that is documentation, not a read.

## Tests

### tests/test_prompt_sweep.py (modify)

Append a new test to the existing file (created in Story 2):

- **test_batch_2_no_hardcoded_mantle_reads**: Same regex-based check as Story 2, but for the 7 files in this batch (`design-product.md`, `design-system.md`, `distill.md`, `fix.md`, `idea.md`, `implement.md`, `plan-issues.md`).
- **test_batch_2_includes_resolve_prelude**: Asserts each of the 7 files contains `MANTLE_DIR=$(mantle where)`.

Constants to add to the file:

```python
BATCH_2_FILES = (
    "design-product.md",
    "design-system.md",
    "distill.md",
    "fix.md",
    "idea.md",
    "implement.md",
    "plan-issues.md",
)
```

Reuse the `HARDCODED_READ_RE` and `PROMPTS_DIR` constants defined in Story 2.
