---
issue: 81
title: Tighten verification-strategy handoff to prevent agents skipping config.md
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-21'
confidence_delta: '+1'
tags:
- type/learning
- phase/reviewing
---

## What went well

- **Issue 80's retrospective predicted this exactly.** 80's learning said *"Bundle tier-1 fixes through /mantle:build. Issues 81/82/83 are same-shape small batches — pipe them through /mantle:build directly rather than manually shaping each — the rubric fits."* Confirmed: 1 story, 1 code commit (bcbbd7e), 4/4 ACs passed on first verify, no retries, no blockers, no human-in-the-loop corrections.
- **Meta-template carve-out earned its keep.** Slice was `claude-code` only and files were Mantle's own `claude/commands/mantle/*.md` templates, so shaping reported "no vault skills applied — meta-template edit" and satisfied Iron Law #5 by naming zero skills (the carve-out removes the floor, not the ceiling). Exactly the scenario the carve-out exists for — no skill-reading theatre on an issue where no vault skill genuinely applies.
- **AC-03 was designed self-verifying.** The acceptance criterion "smoke run against a project with a configured verification_strategy does not invoke mantle introspect-project" is satisfied by the verify run against this project (which has a populated verification_strategy). The AC proves itself by being executed. Clean framing — copy this pattern for future "behaviour under configured state" criteria.
- **Simplify correctly skipped.** 0 src/tests files changed (prose-only edit in claude/) → diff-stats reported 0/0 → below threshold. The simplifier scope is src/+tests/ only, so claude-code-slice edits pass through cleanly.

## Harder than expected

- **migrate-acs re-ran on issues 80 and 81 during verify, even though commit 71271ec backfilled structured ACs for issues 77, 80-86 three days ago.** The verifier reported "issue 81 and issue 80 still had unstructured markdown checkboxes" and ran `mantle migrate-acs` as a one-time prerequisite. Either the earlier backfill didn't persist for these two issues, or migrate-acs is re-syncing frontmatter ↔ body markdown on every run (possibly keeping the `[x]`/`[ ]` checklist in the body in sync with the frontmatter `passes` flags). Minor turn-waster today — the agent handled it inline — but it's a signal that backlog hygiene isn't as stable as commit 71271ec implied. Worth a follow-up to determine whether migrate-acs is idempotent w.r.t. already-migrated issues.

## Wrong assumptions

- None on this run. The issue was crisply scoped from 77's retrospective: config.md first, introspect-project only as fallback, update verify.md and any other command that defers to it. Survey found exactly two sites (verify.md, build.md) and confirmed fix.md was already directive. No scope drift, no false starts.

## Recommendations

- **Pipe 82 and 83 through /mantle:build next.** Same-shape tier-1 fixes (export MANTLE_DIR via Claude Code, make collect-issue-diff-stats source-aware). Both fit the rubric "single logical edit, clear spec, no design judgement" — exactly the shape build automates cleanly. Do not hand-shape them.
- **File a follow-up to investigate migrate-acs behaviour.** Candidate wording: *"Investigate why migrate-acs re-runs on issues previously backfilled by commit 71271ec — determine whether it's (a) the backfill didn't persist, (b) migrate-acs re-syncs body markdown on every invocation, or (c) issue frontmatter drifts when transition commands edit the file without preserving structured ACs."* Low urgency — it's a spinning wheel, not a broken gear.
- **Copy the self-verifying AC pattern.** Future "behaviour under configured state X" criteria should be phrased so that the verify-run itself is the evidence, not a separate invocation. Cheaper to verify, harder to game.
- **Meta-template carve-out guardrail confirmed.** The carve-out in shape-issue.md is working as designed. If a future `claude-code` slice issue genuinely benefits from a skill (e.g. design-review for spotting contradictions across commands), select it — the carve-out removes the floor, not the ceiling.

## Notes on process

- Two clean back-to-back small-batch builds (80, 81) with zero corrections. The /mantle:build → /mantle:review → /mantle:retrospective loop now handles tier-1 fixes as a single muscle. Confidence +1: the pipeline is reliable at small batch appetite; still unproven at medium or large batch, and the migrate-acs quirk is the only loose thread worth tracking.