---
issue: 76
title: init-vault silently skips linking when vault directory already exists
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-19'
confidence_delta: '+1'
tags:
- type/learning
- phase/reviewing
---

## What went well

- **Shaped doc was precise.** The story-implementer agent explicitly reported "Story spec was precise and internally consistent" — no re-spawns needed on either story.
- **Two-story split around a tightly-coupled 2-file change still paid off.** Story 1 (core foundation, returns bool) → Story 2 (CLI consumer) kept each story single-concern and let the transient test failure stay localised to one file during the gap.
- **Simplifier earned its keep on a small issue.** Found three real wins: DRY'd duplicated `console.print()` blank line in the CLI, renamed `already_linked` → `created` so the return statement reads naturally, dropped `test_tilde_expansion` as redundant with `test_creates_subdirectories` (both used `tmp_path / 'vault'`, no real `~` expansion tested). Not noise — would have been merged otherwise.
- **Live E2E verification.** The verifier ran the CLI against real pre-existing/fresh vault directories, not just unit tests. Caught AC2's message phrase and AC4's multi-project flow end-to-end.

## Harder than expected

Nothing significant. One intentional friction point: between Story 1 and Story 2, `tests/cli/test_init_vault.py::test_prints_warning_on_existing` was a known transient failure (the exception it asserted no longer fires). Handled cleanly because Story 1's prompt explicitly predicted it and instructed the agent not to fix it.

## Wrong assumptions

None surfaced. The issue body already prescribed the preferred fix ("Core-level fix is cleaner because it keeps `init_vault` semantically idempotent"), and that call held up.

## Recommendations

- **Keep the 'predict transient test failures' pattern** for any multi-story bug fix that deletes or replaces existing coverage. Explicitly name which test will fail between stories, why, and instruct the story-1 agent not to touch it. Prevents unnecessary rework and false-positive red flags.
- **Flag author-prescribed approaches at shape time.** When the issue body already argues for a specific approach (as issue 76 did), shaping tends to rubber-stamp rather than explore. Not always wrong — small well-understood bugs genuinely don't need 2-3 approaches — but the shape doc should label it "author-prescribed, verified vs alternatives" rather than pretending exploration happened. Consider a shape-mode that skips alternatives when the issue body has a `## Proposed fix` section and shape just validates it.
- **Fast-path eligibility check deserves another look.** This issue had 4 files, 125 lines changed (simplifier above threshold), but the edit itself was genuinely small and well-specified. The 'AC mentions new tests' rule currently forces agent-path for any bug fix with a regression test — almost every bug fix. Consider loosening to: fast-path is eligible if test changes are ≤ 2 test functions AND all production edits fit one file. Not urgent; filing as a thought.