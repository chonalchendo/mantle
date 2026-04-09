---
issue: 44
title: Sweep prompts batch 3 (plan-stories, query, research, retrospective, review,
  revise-product, revise-system)
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a Mantle user running prompts in global storage mode, I want `/mantle:plan-stories`, `/mantle:query`, `/mantle:research`, `/mantle:retrospective`, `/mantle:review`, `/mantle:revise-product`, and `/mantle:revise-system` to find the right `.mantle/` directory automatically so the workflow does not silently break.

## Depends On

Story 1 (the `mantle where` CLI command must exist before prompts can call it).

May run in parallel with Story 2, Story 3 (independent file sets).

## Approach

Mechanical sweep of 7 Claude Code prompt files using the same universal pattern as Stories 2 and 3. Insert the `MANTLE_DIR=$(mantle where)` prelude at the top of Step 1, then substitute every literal `.mantle/...` Read/Grep/Glob target with `$MANTLE_DIR/...`.

## Implementation

### Universal pattern (identical to Stories 2 and 3)

At the top of Step 1, insert the resolve-path prelude:

```markdown
First, resolve the project's .mantle/ directory:

    MANTLE_DIR=$(mantle where)

All subsequent `Read` and `Grep`/`Glob` calls in this prompt must use
`$MANTLE_DIR/...` in place of `.mantle/...`.
```

### claude/commands/mantle/plan-stories.md (modify)

Sweep all `.mantle/state.md`, `.mantle/issues/`, `.mantle/shaped/`, `.mantle/product-design.md`, `.mantle/system-design.md`, `.mantle/stories/`, `.mantle/learnings/` Read targets.

### claude/commands/mantle/query.md (modify)

Sweep the vault-source list at Step 3 (every `.mantle/learnings/`, `.mantle/decisions.md`, `.mantle/sessions/`, `.mantle/brainstorms/`, `.mantle/research/`, `.mantle/scouts/`, `.mantle/shaped/` entry becomes `$MANTLE_DIR/...`). Note: the citation-format example at line ~73 (`"(source: .mantle/learnings/issue-27.md)"`) is illustrative formatting guidance, not a Read target — leave it alone.

### claude/commands/mantle/research.md (modify)

Sweep all `.mantle/state.md`, `.mantle/idea.md`, `.mantle/research/` Read targets.

### claude/commands/mantle/retrospective.md (modify)

Sweep all `.mantle/state.md`, `.mantle/issues/`, `.mantle/learnings/`, `.mantle/stories/` Read targets.

### claude/commands/mantle/review.md (modify)

Sweep all `.mantle/state.md`, `.mantle/issues/`, `.mantle/reviews/`, `.mantle/stories/` Read targets.

### claude/commands/mantle/revise-product.md (modify)

Sweep all `.mantle/state.md`, `.mantle/product-design.md` Read targets.

### claude/commands/mantle/revise-system.md (modify)

Sweep all `.mantle/state.md`, `.mantle/system-design.md`, `.mantle/product-design.md` Read targets.

#### Design decisions

- **Identical prelude wording**: must match Stories 2 and 3 exactly so a single grep can verify all sweep stories.
- **Citation examples are not reads**: Strings inside literal example output (like `"(source: .mantle/learnings/issue-27.md)"`) are formatting guidance for the Claude session's response, not Read tool targets. They are documentation and stay as-is.

## Tests

### tests/test_prompt_sweep.py (modify)

Append a new test to the existing file (created in Story 2, extended in Story 3):

- **test_batch_3_no_hardcoded_mantle_reads**: Same regex check as previous batches, scoped to the 7 files in this batch.
- **test_batch_3_includes_resolve_prelude**: Asserts each file contains `MANTLE_DIR=$(mantle where)`.

Constants to add:

```python
BATCH_3_FILES = (
    "plan-stories.md",
    "query.md",
    "research.md",
    "retrospective.md",
    "review.md",
    "revise-product.md",
    "revise-system.md",
)
```

Reuse `HARDCODED_READ_RE` and `PROMPTS_DIR` from the test file.
