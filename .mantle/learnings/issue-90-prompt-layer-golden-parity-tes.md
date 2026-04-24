---
issue: 90
title: Prompt-layer golden-parity test harness for top commands
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-24'
confidence_delta: '+1'
tags:
- type/learning
- phase/reviewing
---

## What went well

- **Shape chose the right approach.** Three approaches considered; B (in-process direct-call + inline_snapshot) was smaller than A (subprocess dual-run) and more complete than C (pure snapshot, no helper). Landed in small-batch appetite and hit all 7 ACs.
- **Test-only addition — zero src/mantle/ surface changes.** Harness lives entirely under tests/parity/, so import-linter contracts stayed untouched and architecture risk was nil. Good default for regression nets: keep them test-side.
- **Three-story split was cleanly parallelizable.** Story 1 (foundation) and story 3 (policy + docs) were marked independent and shipped in one commit (ecf78ac); story 2 built on story 1 (f9d7f79). No blocking dependencies got in the way.
- **Post-build refactor (92f1875) applied the story-2 learning immediately.** Rather than deferring "widen baseline type + fold per-command tests to one-line pattern" to future work, it shipped as the final commit of the issue. Harness landed polished, not merely passing.
- **Zero new runtime deps.** inline-snapshot + dirty-equals already in [dependency-groups.check] — shape noted this explicitly and it held.

## Harder than expected

- **inline_snapshot.snapshot() doesn't satisfy a `baseline: str` signature.** `snapshot()` returns an `EqValue` proxy that only implements `__eq__`; harness code doing `baseline.splitlines()` blew up. Workaround shipped in story 2 (separate `baseline=""` + `assert result.current_text == snapshot()`), then widened in the 92f1875 refactor. Already captured as a story-level learning.
- **Build telemetry is still only partially fixed.** Issue 91 patched session-id writing (confirmed: build 90 has real 12:49/13:14 timestamps vs 88/91 pre-fix had `0001-01-01` placeholders). But build-90's report still says "No story runs detected in this build" — `group_stories()` needs sidechain turns, and either /mantle:build didn't delegate to sub-agents this run or there's a second attribution gap past 91's scope. Worth a follow-up bug rather than a retrospective fix.

## Wrong assumptions

- **"Issue 91 fixed telemetry" was only partially true.** Session-id write works; story-run clustering into the build report is still empty. Scoping of 91 didn't cover this, and nobody checked end-to-end build-file completeness post-fix. Next telemetry issue should demand a full-roundtrip test on a real build — not just the session-id write.
- **Harness signature assumed plain string baselines would compose with inline_snapshot.** The EqValue proxy breaks that. Design-time check: whenever a helper API will accept a snapshot() value, the type must be `EqValue | str` (or the value must flow the other direction — return it for the caller to assert).

## Recommendations

- **File a follow-up bug for story-run attribution in build reports.** Needs: (1) confirm whether /mantle:build should spawn `story-implementer` sub-agents producing sidechain turns, (2) if yes, why build-90 had zero sidechain turns, (3) add an integration test that runs a fake build and asserts the report contains a non-empty `stories:` list.
- **When a harness interacts with inline_snapshot, design around the EqValue proxy upfront.** Either widen the signature to `EqValue | str`, or have the harness return the captured text and make the caller assert against `snapshot()`.
- **Repeat the "apply story-level learnings before marking issue done" pattern.** 92f1875 shows the value of a post-build polish pass when a learning surfaces mid-implementation. Cheaper now than in a future refactor.
- **For future test-infrastructure issues, shape explicitly for "harness self-test" separately from "consumer test."** Story 1's `test_harness.py` was the right call — without it, the broken `baseline.splitlines()` would have been caught only once a per-command test tried to use the helper.