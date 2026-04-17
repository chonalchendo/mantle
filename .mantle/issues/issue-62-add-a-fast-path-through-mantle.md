---
title: Add a fast-path through /mantle:build for trivial single-file edits
status: implementing
slice:
- claude-code
- cli
story_count: 1
verification: null
blocked_by: []
skills_required:
- CLI design best practices
- Design Review
- DuckLake
- Python 3.14
- Python package structure
- SQLMesh Best Practices
- cyclopts
- docker-compose-python
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

`/mantle:build` is a 9-step pipeline (prerequisites → select → skills → shape → plan → implement → simplify → verify → summary) that spawns at least two agents (story-implementer for implementation, a general-purpose agent for verification). It was designed for substantive work — multi-file changes, new CLI surface, new tests, design decisions.

Issue 60 (just shipped) exposed that the pipeline is overkill for genuinely trivial changes:

- The shaped Strategy was "delete 23 lines and one TaskCreate entry in a single template file".
- No tests applied — it was a pure documentation edit.
- The implementation step still spawned a story-implementer agent to do the three-second edit.
- The verification step still spawned a general-purpose agent to confirm the six acceptance criteria.
- Wall time: ~15 minutes. Substantive effort: under 2 minutes.

The retrospective for issue 60 captures this explicitly as "pipeline overhead felt heavy for a 1-line docs edit" and recommends "a lighter path for trivial single-file docs edits."

## What to build

A fast-path in `/mantle:build` that, when the shaped Strategy describes a genuinely trivial change, skips the story-implementer agent spawn and does the edit inline, preserving the rest of the pipeline's safety properties (simplify-skip threshold, verify agent, review handoff).

Shaping decides the concrete trigger and scope. Candidates to evaluate:

- **Trigger A (signal from shape):** shape-issue emits a `fast_path: true` / `fast_path: false` frontmatter field; build reads it. Pro: explicit, hard to get wrong. Con: adds a new shaping decision.
- **Trigger B (heuristic on the shaped doc):** build inspects the shaped Strategy — if it names a single file, describes a removal/rename/one-line change, and no AC requires new tests, skip the implementer agent. Pro: zero shaping overhead. Con: heuristic, can miss.
- **Trigger C (slice signature):** build checks the issue slice. If the slice is exactly `[claude-code]` (docs only), take the fast path. Pro: cheap. Con: too narrow — other trivial edits exist (e.g. fixing a typo in CLI help text).

Whatever the trigger, the fast-path step must still:

- Run `just check` (or the project's check command) after the edit.
- Apply the simplify skip threshold (already in place: files ≤3 AND lines_changed ≤50).
- Spawn the verify agent — verification is the authoritative quality gate per the Iron Laws and must not be short-circuited.

Do NOT remove the story-implementer agent spawn path. The fast-path is an *additional* branch, not a replacement.

## Acceptance criteria

- [ ] Shaped doc names the chosen trigger (A, B, C, or a mix) and gives the rationale.
- [ ] `build.md` documents the fast-path branch with a clear skip condition, following the same "skip when X, otherwise run Y" format that the simplify step already uses.
- [ ] The fast-path branch still runs `just check` and the verify agent — the Iron Laws about verification evidence remain intact.
- [ ] A new regression check (test or template assertion) confirms the fast-path cannot skip Step 8 (Verify).
- [ ] Issue 60's profile (single-file docs edit, no new tests) would have taken the fast-path if re-run.
- [ ] `just check` passes.

## Blocked by

None

## User stories addressed

- As a Mantle user running `/mantle:build` on a trivial docs fix, I want the pipeline to spend effort proportional to the change so that the workflow stays the right tool for both large and small issues.
- As a Mantle contributor maintaining the build pipeline, I want the fast-path to be a named explicit branch with its own safety rules so that future edits do not silently erode verification guarantees.