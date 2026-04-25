---
issue: 92
title: 'Per-stage build telemetry: sub-agent JSONL read path + universal stage-begin
  primitive'
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-25'
confidence_delta: '+1'
tags:
- type/learning
- phase/reviewing
---

## What Went Well

- **D-revised held under a mid-shape scope expansion.** Started at A (mechanical read-path fix), pivoted through B/C, landed on D when the user's "every LLM-invoking template, not just build" constraint surfaced. The resulting issue body still planned and built cleanly: 5 stories, 6 implement runs + 1 simplify + 1 verify, zero re-shape. Same pattern that worked for 89's split — let shape *complete* the rotation rather than locking on the first viable approach.
- **Dead code deleted in the same pass, not deferred.** `_aggregate_cluster`'s sidechain branch, `Marker`, `MarkerWindowWarning`, `_attach_story_ids`, and `cli/builds.py:_derive_mtime_markers` all went out alongside the new path. Module ended narrower than it started despite adding sub-agent + stage-window read logic. Avoided the "old fallback for safety" trap that Approach A would have left behind.
- **Single-event marker beat begin/end pairs.** "Next mark closes prior window" eliminated all orphan-end bookkeeping for crashes/resumes — a real cost C would have paid. Single insight; large simplification downstream.
- **Per-session filename storage (`stages-<session_id>.jsonl`) was the right co-location call.** Filename-as-key removes cross-worktree write races by construction; sits next to `baseline-*.md` artefacts so the telemetry folder stays cohesive. This kind of "key in the path, not the body" pattern keeps recurring as the right shape (matches Claude Code's own `<slug>/<session_id>.jsonl` layout).
- **Parity harness absorbed the template churn.** ~16 templates touched, every parity baseline refreshed via `--inline-snapshot=review`, no surprise regressions. This is the dividend that issue 90's harness was built to pay; it paid here.

## Harder Than Expected

- **Shape rotated 4 times before landing.** A → B → C → D-revised. The user-driven scope expansion ("universal, not just build") didn't surface until partway through shaping. Lower-cost-of-rotation in shape than in implement, but still: a scope-expansion question ("does this work outside `/mantle:build`?") belongs near the *top* of every shape session for telemetry/instrumentation work, not as a late surprise.
- **Template skip-list was implementer judgement, not mechanical.** Shape proposed a skip set (`help.md`, `resume.md.j2`, `status.md.j2`, `add-issue.md`, `add-skill.md`, `bug.md`, `inbox.md`, `query.md`) and explicitly punted final decisions to story time. Implementer had to actually evaluate "wiring vs LLM-reasoning" per template. Took longer than a one-line shell-edit per template would suggest. Cheap in absolute terms; worth naming as judgement-not-mechanics in future shapes.
- **`general-purpose → verify` is a lurking trip-wire.** Single-mapping bet acceptable while `build.md` is the only caller — but the moment a future template spawns `general-purpose` for something other than verify, `StoryRun.stage` will silently mislabel. Documented as a "Does not" in the shape; still feels like a future-debt commit.

## Wrong Assumptions

- **"Sub-agent transcripts live as sidechain turns in the parent JSONL" was wrong by the time we got here — but the diagnosis happened in 89's shape, not 92's.** This isn't a 92 wrong-assumption per se; it's a confirmation that 89's diagnostic step (counting sidechain turns in build-90, finding zero) was the load-bearing piece of evidence. Without 89's shaping pre-work, 92 would have started from the wrong premise. Lesson: when issue X is blocked on issue Y, the diagnostic that defines Y can validly happen during X's shape.
- **No 92-specific assumption-break shipped.** The Approach D-revised contract held: stage-begin marks plus sub-agent file globbing produced the attribution rows in build-92 directly. Follow-up commits (`8376e7b cost_usd`, `13935c2 story_id`) were 89-era work on a *different* layer (price/identifier resolution) — they touched the same telemetry surface but were not 92 contract gaps.

## Recommendations

- **Add a "scope-boundary" question to the shape template.** When an issue is instrumentation/telemetry/cross-cutting, ask explicitly: "does this need to work outside its primary entry point?" 92's user-driven expansion ("universal, not just `/mantle:build`") was the right call but should have been a *first*-pass shape question, not a mid-shape pivot. One added line in shape's checklist; saves one rotation per issue of this class.
- **Promote "judgement-not-mechanics" as an explicit task-time tag in plan-stories.** When shape says "implementer decides at story time" (template skip-list, mapping table cut-off, etc.), the planner should attach a "needs judgement" flag on that story — surfaces the implicit cost up-front so estimates stay honest.
- **When deleting along with a rewrite, list the deletions in shape's `Does not` section.** Did this here (`Marker`, `_derive_mtime_markers`, etc.) and it paid off — implementer didn't have to discover the dead-code in flight. Worth promoting to a shape-template convention: every rewrite issue lists what's also removed.
- **Single-event markers are the better default for "X happened" telemetry.** When the question is "what stage was active during this turn?", begin-only markers + "next-begin closes prior" are simpler than begin/end pairs. Reach for the pair shape only when stage-failure detection is the load-bearing requirement (and we don't have one yet).