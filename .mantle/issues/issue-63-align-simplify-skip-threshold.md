---
title: Align simplify skip-threshold stats with simplify scope
status: implementing
slice:
- cli
- claude-code
story_count: 1
verification: null
blocked_by: []
skills_required:
- CLI design best practices
- Design Review
- cyclopts
- inline-snapshot
- omegaconf
- python-314
tags:
- type/issue
- status/implementing
---

## Parent PRD

product-design.md, system-design.md

## Why

Surfaced in issue 62's retrospective (2026-04-17). `/mantle:build` Step 7 gates simplification on `mantle collect-issue-diff-stats --issue {NN}`, which currently counts *all* changed lines across the repo. The simplification agent, however, is scoped to `src/` + `tests/` via the Step 7 diff filter (`git diff --name-only $PRE_IMPLEMENT_REV..HEAD -- src/ tests/`).

Concrete miss from issue 62:
- `collect-issue-diff-stats` reported `files=2, lines_changed=55`.
- After filtering to `src/` + `tests/`, only `tests/test_workflows.py` remained in scope with 17 changed lines.
- The 55-line count tripped the `lines_changed ≤ 50` skip condition, so simplify ran — on 17 lines of test code that had nothing to simplify. One trivial case-fold edit was produced; the agent spawn was otherwise wasted.

This is the third Mantle-internal issue in a row where Step 7 fired on a diff dominated by `.md` prose in `claude/` — a path the simplifier cannot touch. The gate and the scope are talking past each other.

## What to build

Two things need to agree on what "counts":

1. **Stats source.** `collect-issue-diff-stats` either (a) defaults to the same `src/` + `tests/` filter Step 7 uses, or (b) gains a `--scope` flag so build.md can request the filtered count explicitly. Prefer (b) if other callers want the full count; prefer (a) if Step 7 is the only caller today.
2. **Step 7 gate prose.** `claude/commands/mantle/build.md` must read whatever stat aligns with its own scope filter, without the reader having to cross-reference two definitions of "trivial".

Shaping should pick the concrete path. The choice hinges on whether `collect-issue-diff-stats` has any caller besides Step 7 — a grep across the codebase answers it.

## Acceptance criteria

- [ ] Shaped doc names which of (a) default-filter or (b) `--scope` flag is chosen, with the grep evidence for why.
- [ ] `collect-issue-diff-stats` and Step 7's simplifier scope agree on what "changed lines" means, by construction (not by reader memory).
- [ ] For issue 62's commit range, the gate would now correctly skip simplification (lines_changed for `src/` + `tests/` is 17, below 50).
- [ ] A new test covers the scope alignment: either a unit test on `collect-issue-diff-stats` that asserts it excludes `claude/` paths by default (or via flag), or a template assertion that build.md's diff-stats call and its scope-filter line refer to the same paths.
- [ ] `just check` passes.

## Blocked by

None.

## User stories addressed

- As a Mantle user running `/mantle:build` on an issue whose diff is mostly `.md` prose, I want the simplify step to skip correctly rather than spawning a refactorer agent with nothing to refactor, so the pipeline's cost matches the work it can actually perform.
- As a Mantle contributor reading `build.md` Step 7, I want the gate condition and the scope condition to be visibly aligned, so I do not have to reason across two definitions of "what counts as a line changed".