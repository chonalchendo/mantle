---
issue: 91
title: Fix SessionStart hook to write .mantle/.session-id from payload
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-24'
confidence_delta: '+1'
tags:
- type/learning
- phase/reviewing
---

## What went well

- **Bug → issue → shape → build → verify pipeline ran clean.** Live telemetry rot was caught in a brainstorm, filed as a bug, opened as issue 91 with a clear root-cause note, shaped once (A chosen, B rejected on 'pull complexity down'), built end-to-end via `/mantle:build`, verified with 6/6 ACs PASS. This is the same pipeline shape issue 80 and 84 retros validated — it keeps working for well-scoped, single-slice fixes.
- **Shape doc right-sized for a 15-LOC hook patch.** One approach chosen, one rejected with a one-line reason. No wasted cycles. The shape artifact was ~80 lines for a ~15-LOC change, which is the right ratio because the *decision* (extend hook vs add CLI surface) carried most of the value, not the code itself.
- **Single-story decomposition matched the scope.** `plan-stories` produced 1 story; no dependency web to manage; implementer + simplifier + verifier in one automated pass.

## Harder than expected

- **ac-03 / ac-04 couldn't be verified live — had to accept DONE_WITH_CONCERNS.** A fresh Claude Code session can't be started from inside a running one, and a real `build-start` / `build-finish` against a new session UUID needs that fresh session. Code-path inspection plus hook tests stood in. This is a recurring shape of limitation (hooks, MCP lifecycle, anything environment-lifecycle-coupled) — future shaping for this class should name the verification gap up front and either spec a mechanical substitute or explicitly pre-waive.
- **Structured ACs were empty at review time — had to run `mantle migrate-acs` mid-flow.** Issue 91 predated structured ACs, so `mantle list-acs --issue 91 --json` returned `[]` even though the body had 6 criteria. Migration was a one-liner, but the review command should probably auto-migrate before loading, or `/mantle:verify` should migrate on first run. Worth a small follow-up issue.
- **AI implementer left two trivial bloat bits** (unhoisted pytest import + a redundant comment) that a manual refactor pass caught (commits `7c1caa0`, post-feat). Small-batch work still benefits from a `/mantle:simplify` or manual review pass — this matches the simplify-threshold learnings from issues 62 / 63.

## Wrong assumptions

- **Assumed `CLAUDE_SESSION_ID` would be set in the hook env.** It isn't, and never has been. The fallback chain in `core/telemetry.py:current_session_id()` was written against that assumption, so the resolution always fell through to a stale file. Lesson: when a docstring says 'the X hook writes Y', grep to confirm Y is actually written before trusting the chain. This is the same class of silent-assumption rot that issue 77's machine-verifiable-AC work was meant to catch at the code boundary.
- **Assumed silent telemetry rot would surface fast.** It sat for 8 days across 15 build files before anyone noticed. Nothing in `/mantle:status` or the build output surfaces 'same session UUID across N consecutive builds'. Issue 89 (A/B harness) will naturally exercise this when it reads telemetry — so I'm not filing a standalone health-check issue, but 89's shape should include a 'detect all-builds-same-UUID' guard as a canary, which would catch this regression class going forward.

## Recommendations

- **Name the 'lifecycle-environment' verification-gap pattern in shaping.** When an issue modifies a hook, session-start, MCP server lifecycle, or anything whose effect is only observable in a *new* environment instance, the shape doc should explicitly list ACs that will be DONE_WITH_CONCERNS and what mechanical substitute (tests, code-path read) stands in. Stops the last-mile verify friction.
- **Auto-migrate structured ACs in `/mantle:verify` (and `/mantle:review` as a fallback).** `mantle migrate-acs` is idempotent and fast; calling it at the top of verify would eliminate the 'empty JSON' surprise on legacy issues. Small issue candidate.
- **Fold a telemetry canary into issue 89's shape.** When the A/B harness reads build files, it should flag the 'all-builds-share-one-session-id' case as a data-health warning. Cheap to add at shape time; would have caught this regression in ~1 build instead of 15.
- **Keep the `/mantle:build` + manual simplify-review pattern.** `/mantle:build` shipped the correct implementation; a ~2-minute manual pass caught two trivial idiomatic bits. Either automate that pass (extend simplifier's triggers) or keep it as a documented post-build step.