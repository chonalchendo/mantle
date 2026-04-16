---
title: Fix redundant skill-loading step in /mantle:plan-stories
status: planned
slice:
- claude-code
- cli
- core
- tests
story_count: 0
verification: null
blocked_by: []
skills_required: []
tags:
- type/issue
- status/planned
---

## Parent PRD

product-design.md, system-design.md

## Why

The `plan-stories.md` command template has a "Step 5c — Load relevant skills" section that runs `mantle update-skills --issue {NN}` and `mantle compile` at the end of story planning, with the stated purpose of "ensuring the right vault knowledge is available for implementation."

This narrative is misleading. `implement.md:180-182` explicitly states:

> Skill context: Skill knowledge is embedded in the shaped issue's code design. The implementing agent reads the shaped issue — do NOT separately inject skill files — the story spec already carries the relevant knowledge.

So the implementer doesn't read skill files. It relies on skill knowledge being baked into the shaped doc during `/mantle:shape-issue`. That means step 5c is doing metadata bookkeeping (updating `state.md:skills_required`), not preparing context for a downstream consumer.

For contrast: `build.md` (the one-shot shape-plan-implement command) loads skills at its step 3, because it does the shaping itself.

**Why this is genuinely redundant:**

- Shaping bakes design decisions (SQL patterns, kinds, grains, framework specifics) into the shaped doc using skill knowledge.
- Planning decomposes the shaped doc into stories — it's a slicing exercise, not a design exercise. Vault skills don't meaningfully sharpen story specs.
- Implementation reads the shaped doc + story spec, which already encode the knowledge.
- In the last `plan-stories` run, `update-skills` auto-detected `dirty-equals` and `inline-snapshot` as "new skills" because story bodies contained test-assertion phrasing — pure false positives; neither library is used in the codebase.

## What to build

A corrective edit to `plan-stories.md` that removes the misleading "ensure skills are available for implementation" framing. The decision between three options (cut entirely / shrink to one-line bookkeeping / move to shape-issue only) is deferred to `/mantle:shape-issue` after an investigation pass confirms whether `skills_required` is consumed anywhere load-bearing downstream.

### Flow

1. Shaping agent reads `plan-stories.md`, `implement.md`, `shape-issue.md`, and `build.md` under the templates directory.
2. Confirms whether `implement.md` actually reads skill files anywhere, or whether it truly relies on the shaped doc. Checks subagents spawned by implement for skill loading behaviour.
3. Checks whether the `skills_required` list in `state.md` is consumed anywhere load-bearing downstream, or only by display commands (status, resume).
4. Chooses one of: (a) cut step 5c entirely if `skills_required` metadata is purely display, (b) shrink to one-line bookkeeping while dropping the narrative framing and "skill gaps" user-facing section, (c) move the logic to `shape-issue.md` only since that's the phase where skills actually inform design.
5. Applies the chosen edit to `plan-stories.md` — show diff before applying.
6. If the investigation reveals `implement.md` should be loading skills but currently doesn't, file a separate follow-up issue; do NOT fix it in this pass.

## Acceptance criteria

- [ ] Investigation report (under 150 words) captures whether `implement.md` and any subagents it spawns actually read skill files, and what `skills_required` in `state.md` is consumed by.
- [ ] A proposed edit to `plan-stories.md` is shown as a diff before being applied.
- [ ] `plan-stories.md` no longer presents the skill-loading step as context-priming for implementation — either cut, shrunk to bookkeeping, or moved to shape-issue, per the chosen option.
- [ ] `shape-issue.md` and `implement.md` are NOT modified in this issue (scope is strictly plan-stories.md).
- [ ] If the investigation finds `implement.md` should be loading skills but currently doesn't, a separate follow-up issue is filed capturing that gap.
- [ ] `just check` passes.

## Blocked by

None

## User stories addressed

- As a Mantle user planning stories, I want command documentation to accurately describe what each step does so that I can trust the workflow and not be misled by narrative that doesn't match runtime behaviour.
- As a contributor maintaining Mantle's command templates, I want internal consistency between `plan-stories.md` and `implement.md` so that future changes don't compound the inconsistency.