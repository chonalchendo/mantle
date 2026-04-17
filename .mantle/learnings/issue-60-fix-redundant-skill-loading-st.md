---
issue: 60
title: Fix redundant skill-loading step in /mantle:plan-stories
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-17'
confidence_delta: '+1'
tags:
- type/learning
- phase/reviewing
---

## What Went Well

- **Smallest-appetite rule fired cleanly.** Shape-issue picked option (a) (cut entirely) over shrinking or moving the logic. One-file, 1+/23- diff, single commit. No churn.
- **Investigation was the real deliverable.** The shaped doc's `## Investigation` section answered both sub-questions (what consumes `skills_required`, does `implement.md` load skills) with cited line numbers. AC1 essentially collapsed into the shaping step.
- **Pre-implementation grep for `skills_required` consumers surfaced the load-bearing path** (`core/compiler.py`) vs display-only consumers (`resume.md.j2`, `status.md.j2`) in one pass. No rabbit hole.
- **Simplification skip-threshold worked.** Files ≤3 AND lines_changed ≤50 correctly bypassed the step — the 1+/23- diff had nothing to simplify.

## Harder Than Expected

- **Pipeline overhead felt heavy for a 1-line docs edit.** Shape → plan → implement → verify → review spent ~15 minutes of wall time and two agent spawns on what was structurally a `git rm` of 23 lines. Worth asking whether `/mantle:build` is the right vehicle for single-file docs edits.
- **Auto-commit hook split the work across two commits.** `7f07f8d` bundled `.mantle/` bookkeeping as `chore(mantle): session` and `001fd35` held the actual fix. Benign, but the bookkeeping commit's message ("Implemented story 1 of issue 60") overstates what it contains (only `.mantle/` artefacts, no source).
- **Verifier flagged the investigation report at 198 words against the 150-word AC and accepted it anyway.** Fuzzy word-count ACs create a "spirit vs letter" judgement call every time.
- **Confirmed the archived-issue bug on `mantle save-learning`.** Retrospective runs after approval, which archives the issue, but save-learning rejects issues not in `.mantle/issues/`. Had to temp-copy the archived file back to run the command. This bug was already noted in the issue-51 retrospective — it still stands.

## Wrong Assumptions

- **Assumed `implement.md` might have a real gap in skill-loading that would need a follow-up issue filed.** Reading Step 3 (lines 94-99) disproved this immediately — it already runs `update-skills + compile`. The issue body's AC5 ("file follow-up if implement doesn't load skills") anticipated a gap that didn't exist.
- **Shape-issue's "select 2-4 skills" rule produced weak matches.** This was a meta-template edit, not a tech-stack task. The two skills Read (`design-review`, `cli-design-best-practices`) contributed general "YAGNI / delete" principles but no pattern specific to the work. Iron Law #5 still applied, but signal-to-noise was thin.

## Recommendations

- **File a follow-up issue for `implement.md`'s internal inconsistency.** Open question from the shaped doc still stands: Step 3/4 list `.claude/skills/*/SKILL.md` as orchestrator context, but lines 180-183 tell the story-implementer "do NOT separately inject skill files." Out of scope for 60, valid for its own issue.
- **Consider a lighter path for trivial docs edits.** When the shaped Strategy is "delete N lines of a single template file with no AC requiring tests," the full `/mantle:build` pipeline is overkill. Candidate: short-circuit to direct edit + `just check` + commit + review, skipping the story-implementer agent spawn.
- **Drop or soften word-count caps on investigation-style ACs.** "Under 150 words" creates verifier-side judgement churn. Either measure something objective (sections present, questions answered) or accept that investigation reports need room.
- **Keep the shape-issue "investigation first" pattern.** For issues where the real question is "does X behave the way we think it does?", the Investigation section of the shaped doc IS the deliverable. Story planning and implementation become mechanical application. Repeat this pattern.
- **Fix `mantle save-learning` to accept archived issues.** Second occurrence of this bug (first noted in issue-51 retrospective). The documented flow (review → archive → retrospective) is incompatible with the CLI's current check.