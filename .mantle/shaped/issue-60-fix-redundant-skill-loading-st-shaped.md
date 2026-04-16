---
issue: 60
title: Fix redundant skill-loading step in /mantle:plan-stories
approaches:
- cut Step 5c entirely
- shrink to one-line bookkeeping
- move skill auto-detection to shape-issue
chosen_approach: cut Step 5c entirely
appetite: small batch
open_questions:
- Should implement.md's own skill-loading guidance (Step 3 reads .claude/skills/ but
  Step 5 says not to inject) be reconciled in a follow-up issue?
author: 110059232+chonalchendo@users.noreply.github.com
created: '2026-04-16'
updated: '2026-04-16'
updated_by: 110059232+chonalchendo@users.noreply.github.com
tags:
- type/shaped
- phase/shaping
---

## Investigation

**What consumes `skills_required`:**

- **Load-bearing:** `core/compiler.py` reads `state.md:skills_required` (and the issue's own `skills_required` list) to select which skill nodes to compile into `.claude/skills/`. Updating the list changes what gets compiled next time.
- **Display only:** `claude/commands/mantle/resume.md.j2` and `status.md.j2` render the list as part of status output.

**Does `implement.md` read skill files?** Partly — and that is the crux:

- `implement.md` Step 3 (lines 94-99) already runs `mantle update-skills --issue {NN}` and `mantle compile --issue {NN}` before story implementation starts. This is strictly redundant with `plan-stories.md` Step 5c.
- `implement.md` Steps 3/4 list `.claude/skills/*/SKILL.md` as context for the orchestrator when selecting per-story context briefs.
- `implement.md` lines 180-183 explicitly tell the story-implementer agent: \"do NOT separately inject skill files — the story spec already carries the relevant knowledge.\"

**Therefore:**

- Skill-knowledge flow into implementation happens via the shaped doc → story spec path, not via skill files at planning time.
- `update-skills + compile` in plan-stories Step 5c adds no value — implement.md does the same work moments later.
- The \"skill gaps detected\" user-facing section pushes `/mantle:add-skill` at a point where creating a skill changes nothing the plan-stories run can act on (implement.md will auto-detect and compile anyway).

## Approaches considered

### (a) Cut Step 5c entirely *(chosen)*

- Remove Step 5c section and its TaskCreate entry from the top of `plan-stories.md`.
- Let `implement.md` Step 3 be the single owner of `update-skills + compile` for the implement path.
- **Appetite:** small batch (single-file docs edit).
- **Pros:** smallest change, removes the misleading framing completely, aligns with the issue's core observation (planning is a slicing exercise, not a design exercise).
- **Cons:** developers who do not immediately proceed to implement won't see the \"skill gaps\" hint.
- **Mitigation for cons:** the hint is available via `/mantle:add-skill` at any time and is also displayed by `/mantle:shape-issue`.

### (b) Shrink to one-line bookkeeping

- Keep the `mantle update-skills --issue {NN}` call but delete the narrative framing, the \"skill gaps\" user-facing section, and the `mantle compile` call.
- **Appetite:** small batch.
- **Rejected because:** still leaves a redundant `update-skills` call that `implement.md` Step 3 repeats immediately — the deletion is cleaner.

### (c) Move auto-detection into shape-issue

- Shape-issue already has its own Load skills step (lines 69-92) where the user manually selects 2-4 skills to Read.
- Adding a separate auto-detection call there would duplicate that selection or conflict with it.
- **Rejected because:** shaping's manual skill selection and the auto-matcher have different purposes; mixing them muddies the shape-issue flow.

## Strategy

Single-file documentation edit to `claude/commands/mantle/plan-stories.md`:

1. Remove the \"Step 5c — Load relevant skills\" section (lines 233-252).
2. Remove the \"Step 5c\" entry from the TaskCreate list at lines 17-27.
3. Renumber nothing else — Step 6 remains Step 6 (Session wrap-up).

Commit message: `docs(issue-60): remove redundant skill-loading step from plan-stories`.

## Fits architecture by

- Respects the `core/` ↔ `cli/` ↔ `claude/` separation from CLAUDE.md — the change is strictly in the Claude Code prompt layer.
- Reinforces the single-owner principle for side effects: `implement.md` owns `update-skills + compile` for the implement path; `shape-issue.md` owns manual skill Reads for the shape path.
- Aligns with `design-review`'s \"YAGNI / Delete code for features not in scope\" guidance — this is dead metadata bookkeeping dressed up as context-priming.

## Does not

- Does not modify `implement.md` or `shape-issue.md` (AC: strictly plan-stories.md scope).
- Does not change the CLI surface of `mantle update-skills`, `mantle compile`, `mantle list-skills`, or `mantle add-skill`.
- Does not add or remove any Python code, tests, or skill files.
- Does not file a follow-up issue about implement.md's skill-loading — the redundancy between plan-stories and implement is fully resolved by this change. A separate internal inconsistency in implement.md (Step 3/4 vs line 180-183 on whether skill files should be read) is noted as an open question but is not an implement-doesn't-load-skills gap.
- Does not touch `resume.md.j2` or `status.md.j2` — they are display consumers of `skills_required` and continue to render whatever the list contains.