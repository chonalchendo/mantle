---
date: '2026-04-22'
author: 110059232+chonalchendo@users.noreply.github.com
title: gsd-scout-backlog-reshape
verdict: proceed
tags:
- type/brainstorm
---

## Brainstorm Summary

**Idea**: Reshape the optimisation-focused backlog in light of the 2026-04-22 GSD scout
**Problem**: GSD has shipped production solutions to much of Mantle's open optimisation backlog; the question is which existing issues collapse, which split, and which net-new threads to open — without widening past the stated optimisation focus.
**Vision alignment**: Strong (per-decision varies — see below)

## Exploration

Four parallel structural decisions, framed by the user up-front. One clarifying exchange surfaced the load-bearing assumption:

- **Q**: Real time horizon on (a) aggressive token cuts and (b) issue 85 (cross-repo)?
- **A**: Both within ~1 month, optimisation lens dominant.

Critical reframe surfaced during context load: **issue 75 is mostly already shipped via 84**. Of 75's 5 ACs, 4 (config, presets, tests, just check) landed in 84's `model-tier` config + `cost-policy.md` work. Only AC-03 (the A/B harness) remains live. The scout's "model-profiles.md drops into 75" claim is ~80% already true — adopting GSD's profile schema now would be a cosmetic refactor of 84's existing shape, not new work.

## Challenges Explored

**Decision 1 (collapse 75+79) — assumption surfacing**: 79's measurement work overlaps with 88's already-shipped audit-tokens infrastructure, not with 75-remainder's harness work. Different work shapes, no shared infrastructure remains to justify collapse.

**Decision 2 (Workflow Routing v1 milestone) — devil's advocate**: Auto-memory rule "resist scope creep in shaping" applies one level up. Bundling four issues by *theme* doesn't mean they share *work*. 71+72 do (72 says so explicitly). 70 and 73 don't.

**Decision 3a (golden harness) — first-principles on scope**: GSD has 103 commands; Mantle has ~25. Replicating the full registry-style harness over-engineers for the surface area. MVP: dual-run on the 3 commands targeted for compression + exception-registry policy test.

**Decision 3b (messaging correction) — pre-mortem**: Backlog issues are for *work*, not *corrections*. Issue-ifying a copy edit defers it indefinitely; treating it as a `/mantle:revise-product` task lands it in one session.

**Decision 4 (extract session-identity ahead of 85) — devil's advocate**: 84 retrospective lesson directly applies — shape-time decisions don't propagate back into ACs unless wired in. Extracting GSD's primitive before shaping 85 risks building the wrong API. 85's own AC-01 mandates a shape doc exploring 2-3 approaches; skipping that for prerequisite work is a category error.

## Approaches Considered

Per-decision approaches captured in conversation; recommended approach for each:

| Decision | Recommended approach | Rejected alternatives |
|---|---|---|
| 1 — 75 status | **Close 75, open clean A/B-harness issue** | Re-scope 75 in place; collapse 75+79 |
| 2 — 70/71/72/73 reshape | **Merge 71+72 only; keep 70 and 73 standalone** | Workflow Routing v1 milestone (scope creep) |
| 3a — golden harness | **Open new issue, 3-command scope** | Full GSD-style registry across all commands |
| 3b — messaging correction | **`/mantle:revise-product` session, no issue** | File as backlog issue |
| 4 — session-identity primitive | **Bundle in 85, shape 85 within ~2 weeks** | Extract primitive ahead of shaping |

## Verdict

**Verdict**: proceed
**Reasoning**: Four structural decisions resolved with concrete actions. The dominant pattern: respect existing scope-discipline lessons (84 retrospective, auto-memory rule on shaping scope creep). Adopt cheap GSD wins where they're genuinely drop-in; resist the temptation to wrap multiple distinct work shapes in a unifying milestone.

**Resulting backlog shape** (delta from current state):

- **Issue 75** → close as obsolete (4/5 ACs shipped via 84). File issue history note.
- **NEW issue (replacing 75-remainder)** — A/B harness for build pipeline, single AC, with explicit "needs fresh `/mantle:build` session to satisfy measurement" callout per the 84 retro lesson.
- **Issue 79** → keep as-is. Optionally split at shape-time: mechanical `@file` include refactor (drop-in GSD pattern) vs `audit-context` CLI on top of 88's primitives.
- **Issue 71** → expand to absorb 72's fresh-context handoff requirement; rename to "Dynamic end-of-command recommendations with fresh-context handoff."
- **Issue 72** → close as merged into 71.
- **Issue 70** → keep separate. Optimisation-flavoured but UX-shaped.
- **Issue 73** → keep separate. Off the optimisation track; revisit prioritisation but don't bundle.
- **NEW issue** — Prompt-layer golden-parity test harness, scoped to 3 highest-cost commands (build, implement, plan-stories), with exception-registry policy test. Enables aggressive token cuts in 79/87/88.
- **Issue 85** → keep, schedule shape session within ~2 weeks. Document GSD env-var → TTY session-identity pattern as lead candidate; story 1 implements the chosen primitive. No prerequisite extraction.
- **Product-design messaging** → no issue. Run `/mantle:revise-product` in a separate session: drop the false "GSD has no runtime" claim; lead differentiators with persistent cross-project knowledge graph + Obsidian-native + cohesive idea-to-review lifecycle.

**If proceeding**: Optimisation queue becomes — (1) `/mantle:revise-product` for messaging fix, (2) shape new A/B-harness issue, (3) shape new golden-harness issue, (4) shape 79, (5) shape 71+72 merged, (6) shape 85 (within 2-week window), (7) revisit 70 and 73 priority after the optimisation slice lands.