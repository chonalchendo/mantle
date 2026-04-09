---
issue: 44
title: Prompt sweep for global storage mode — shape undercount, shared-test-file sequencing
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-09'
confidence_delta: '+1'
tags:
- type/learning
- phase/reviewing
---

## What Went Well

- **`mantle where` design landed clean**: plain `print` (no Rich ANSI), `.resolve()` for absolute guarantee, no side effects, co-located in `cli/storage.py` alongside the other storage commands. 6 unit tests nail local mode, global mode, cwd default, clean output, no-config fallback, and help text.
- **Issue 36's worktree learning propagated correctly**: sequential execution for sweep batches (Stories 2-5) because all four extend `tests/prompts/test_prompt_sweep.py`. No worktree merge pain this time.
- **Shape's rejection of Approach B (CLI owns all reads) and C (symlink) held up**: Approach A (`mantle where` + prompt sweep) is the right-sized solution. Thin CLI wrapper, mechanical prompt edits, honours the existing Bash-for-state + Read-tool-for-content contract.
- **Simplification found real wins**: extracted shared audit helpers (60 lines of duplication) across sweep tests, dropped a vacuous `is_absolute` check. Two consecutive issues where simplification earned its keep.
- **Full-tree audit test is a durable safety net**: going forward, adding a new prompt that reads `.mantle/` directly will fail the test, preventing regression of the global-mode contract.

## Harder Than Expected

- **Shape undercounted the file list by 25%**: shape doc said 20 prompt files, actual was 25 (missed `challenge`, `distill`, `idea`, `query`, `research`). The implementer correctly expanded the sweep, but batch planning had to be adjusted mid-flight.
- **Test relocation churn on review**: initial implementation placed sweep tests in the wrong directory and used a private `project._read_frontmatter_and_body` instead of the public `read_config`. Minor code-review fixes, but both should have been caught at planning time.
- **Integration test documents the real contract, not the spec's wishful one**: `migrate_to_global` leaves a stub `.mantle/config.md` even though global mode's stated constraint is 'no local `.mantle/` artifact'. Test asserts the actual behaviour; gap captured in inbox as a separate bug.

## Wrong Assumptions

- **\"Shape's grep is authoritative\"**: The shape doc's file enumeration can drift from reality (files added between shape and build, or incomplete grep). Implementers must re-verify the file set before batching.
- **\"Parallel worktrees are always faster\"**: Shape called for parallel sweep batches. Reality: all batches extended the same test file, forcing sequential. Prompt sweeps should default to sequential.
- **\"`save-learning` is a neutral read-only command\"** (from inbox): it auto-archives mid-implementation issue files. Noted as a separate bug to fix.

## Recommendations

1. **Shape must run a verifying grep + file count before finalising batches**. When a shape doc enumerates \"N files to change\", the implementer should re-run the exact grep pattern in the current HEAD to detect drift. Specifically, add a \"File enumeration verification\" step to the shape checklist: `grep -l <pattern> <dir> | wc -l` should match the shape's count, and discrepancies should force a batch re-plan before Story 2 starts.

2. **Prompt sweeps default to sequential, not parallel**. Treat any story pattern where multiple stories extend the same test file as a sequential-only pattern. Specifically: if Stories N..M all add tests to `tests/prompts/test_prompt_sweep.py`, shaping should explicitly note \"sequential execution (shared test file)\" in the story decomposition. Reserve worktree parallelism for truly independent slices (different test files, different modules).

3. **Test-placement and public-API conventions belong in planning, not review**. When a new test file is created, plan-stories should specify the exact path (e.g. `tests/prompts/test_prompt_sweep.py`) and call out that tests must use public APIs (`project.read_config`, not `project._read_frontmatter_and_body`). Saves a review round-trip.

4. **Global-mode contract needs a single source of truth**. The spec says \"no local `.mantle/` artifact\" but `migrate_to_global` leaves a stub `.mantle/config.md`. Either fix the migration or update the spec — currently the test documents a contradiction. Captured in inbox as a follow-up.

5. **`save-learning` should not auto-archive mid-implementation issue files**. Captured in inbox as a bug. Retrospectives are read-heavy; they should not mutate issue state as a side effect.