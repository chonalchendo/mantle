---
title: Audit .mantle/ and CLAUDE.md for progressive-disclosure drift
status: planned
slice:
- core
- cli
- claude-code
- tests
story_count: 0
verification: null
blocked_by: []
skills_required: []
tags:
- type/issue
- status/planned
acceptance_criteria:
- id: ac-01
  text: '`mantle audit-context` CLI exists and emits per-file token counts, cross-file
    overlap pairs, and an orphaned-file list for a given directory tree.'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-02
  text: An audit report lives in `.mantle/` (e.g. under learnings/ or a one-off audit
    folder) with metrics for CLAUDE.md, product-design.md, system-design.md, state.md,
    and `.mantle/` artifacts.
  passes: false
  waived: false
  waiver_reason: null
- id: ac-03
  text: The report ends with a ranked trim/split/link action list, each action tagged
    with estimated token savings and a clarity rationale.
  passes: false
  waived: false
  waiver_reason: null
- id: ac-04
  text: Obvious, unambiguous cuts are applied in the same issue (committed), and ambiguous
    ones are filed as follow-up inbox items or issues.
  passes: false
  waived: false
  waiver_reason: null
- id: ac-05
  text: 'Tests cover the measurement CLI: token counting, overlap detection, orphan
    detection.'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-06
  text: '`just check` passes.'
  passes: false
  waived: false
  waiver_reason: null
---

## Parent PRD

product-design.md, system-design.md

## Why

Part 4 of "You are not using AI wrong..." documents a specific failure mode: the "one big AGENTS.md" approach decays silently as a codebase grows. Context crowds out the task, guidance becomes non-guidance, rot is invisible, and coverage is unverifiable. The fix is progressive disclosure — a short, stable entry point that points to deeper sources of truth rather than duplicating them.

Mantle has exactly the surface area this failure mode targets: CLAUDE.md (project instructions), product-design.md and system-design.md (design artifacts, both large), an ever-growing skills list in state.md, a backlog of issues, brainstorms, inbox items. Every `/mantle:build` run depends on these being the right shape. If they're drifting toward "comprehensive dump" quality degrades without a clear cause.

This is an investigation-shaped issue. It is only "critical" in the sense that context drift is invisible — we won't notice it until build quality drops and the cause is already tangled. Cheap to run, high option value, high informational payoff for future cuts.

Note: issue-74 audits `/mantle:*` command prose (the slash commands in `claude/commands/mantle/`). This issue audits project context files (CLAUDE.md and `.mantle/` artifacts) — distinct surface area. Measurement primitives should be general enough that both audits share them.

## What to build

A reusable measurement script plus a one-shot audit report. The script counts tokens per context file, detects cross-file duplication (shingles or section-title overlap), flags orphaned files nothing references via wikilinks or save-X commands, and measures pointer-vs-duplication ratio. The audit report runs the script across CLAUDE.md, product-design.md, system-design.md, state.md, and the `.mantle/` artifact folders. Output is a ranked trim/split/link action list with estimated token savings.

Land obvious cuts in the same issue (clear duplication, stale sections, dead pointers). Anything ambiguous spawns follow-up issues so this one stays bounded.

### Flow

1. A `mantle audit-context` CLI walks a given tree, emits per-file token counts, overlap pairs, and orphan list as structured output (JSON + markdown summary).
2. The audit report (saved as a learning or a one-off file in `.mantle/`) runs the CLI over the live project and documents findings.
3. The report ends with a ranked action list — each action names the file(s), the rationale (duplication / rot / orphan), and an estimated token impact.
4. Obvious cuts are applied in-issue with a diff commit; ambiguous ones are filed as inbox items or follow-up issues.
5. The measurement CLI is kept (not deleted post-audit) so it can be re-run whenever drift is suspected.

## Acceptance criteria

- [ ] ac-01: `mantle audit-context` CLI exists and emits per-file token counts, cross-file overlap pairs, and an orphaned-file list for a given directory tree.
- [ ] ac-02: An audit report lives in `.mantle/` (e.g. under learnings/ or a one-off audit folder) with metrics for CLAUDE.md, product-design.md, system-design.md, state.md, and `.mantle/` artifacts.
- [ ] ac-03: The report ends with a ranked trim/split/link action list, each action tagged with estimated token savings and a clarity rationale.
- [ ] ac-04: Obvious, unambiguous cuts are applied in the same issue (committed), and ambiguous ones are filed as follow-up inbox items or issues.
- [ ] ac-05: Tests cover the measurement CLI: token counting, overlap detection, orphan detection.
- [ ] ac-06: `just check` passes.

## Blocked by

None

## User stories addressed

- As a maintainer, I want visibility into which context files are bloating or drifting so I can cut before quality degrades.
- As an agent running `/mantle:build`, I want the baseline context (CLAUDE.md, product-design, system-design) to be short pointers rather than duplicative dumps so attention lands on the task instead of decoration.
- As a future me re-running the audit six months later, I want a reusable CLI rather than a one-off script so the cost of the next audit is near zero.