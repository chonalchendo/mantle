---
issue: 46
title: Fix save-learning auto-archive breaking /mantle:build pipeline
approaches:
- Remove archive from save-learning, move to transition-to-approved
- Add --no-archive flag to save-learning
- Gate archive on all-stories-done AND status==verified
chosen_approach: Remove archive from save-learning, move to transition-to-approved
appetite: small batch
open_questions: []
author: 110059232+chonalchendo@users.noreply.github.com
created: '2026-04-09'
updated: '2026-04-09'
updated_by: 110059232+chonalchendo@users.noreply.github.com
tags:
- type/shaped
- phase/shaping
---

## Approaches

### (a) Remove archive from save-learning, drive from transition

Remove the `archive.archive_issue()` side effect from the save-learning CLI wrapper. Make archival happen at the terminal issue transition. Save-learning becomes pure — it writes a learning file and updates state, nothing else.

**Tradeoffs:** Cleanest decoupling. Preserves single responsibility. One more transition call handles archival explicitly. Only real loss is the convenience of 'save and tidy up in one step' — which was the bug in the first place.

**Rabbit holes:** Import cycles. `core/archive.py` already imports `core/issues`, so the core transition function cannot call archive without creating a cycle. Solution: call archive from the CLI wrapper after the core transition succeeds.

**No-gos:** Does not add a new `mantle archive-issue` CLI surface. Does not alter `core/archive.archive_issue` semantics. Does not change issue schema.

### (b) Add --no-archive flag to save-learning

Keep auto-archive as the default and add an opt-out flag that `build.md` / `implement.md` pass during mid-pipeline captures.

**Rejected:** Leaves the footgun. Any new call site that forgets the flag re-introduces the bug. Pragmatic but couples learning capture to archival forever.

### (c) Gate archive on 'all stories complete AND status == verified'

Keep the call site but add a guard inside `save-learning` that checks the issue state before archiving.

**Rejected:** Hides the coupling instead of removing it. Adds hidden state-dependent behavior to a capture function. Worse for testability.

---

## Chosen approach: (a) with one refinement

Archive at **transition-to-approved**, not transition-to-verified. Reason: `verified → implementing` is an allowed transition (the review-fail rollback path in `review.py`). Archiving at verified would orphan files when review bounces the issue back to implementing. `approved` is the only truly terminal status, so it is the correct archival point.

**Trade-off acknowledged:** A learning captured AFTER approval (the normal retrospective-after-review flow) writes to `.mantle/learnings/` instead of `.mantle/archive/learnings/`. Acceptable because `find_learning_path` reads from `learnings/` already, so discoverability is preserved. Archive is for tidiness, not correctness.

---

## Strategy

1. **`src/mantle/cli/learning.py`**: Remove the `archive.archive_issue` call (lines 72-79) and the `archive` import. The wrapper becomes a thin pass-through to `core/learning.save_learning` plus a confirmation print.

2. **`src/mantle/cli/review.py`**: In `run_transition_to_approved`, after `_transition(issue, project_dir, 'approved', ...)` succeeds, call `archive.archive_issue(project_dir, issue)` and print a summary line listing the archived file count. This keeps the side effect at the CLI layer, avoiding the core import cycle.

3. **`core/archive.archive_issue`**: No signature or behavior change. It remains the single canonical move function.

4. **Tests**:
   - Regression test (satisfies AC4): set up a mid-pipeline scene (issue at `implementing`, shaped doc, 2+ stories, no learning), call `run_save_learning`, assert every pre-existing file still lives at its original path.
   - `tests/cli/test_learning.py`: update any 'save-learning archives' assertions to assert the opposite.
   - `tests/cli/test_review.py`: add 'transition-to-approved archives' test asserting that the issue, stories, and shaped doc are moved when approving.
   - `tests/core/test_archive.py`: unchanged — `archive_issue` semantics unchanged.

## Fits architecture by

- Honours the `core/` → never imports from `cli/` boundary (CLAUDE.md). Core `issues.py` gains no archive dependency — the side effect lives in the CLI wrapper.
- Retrospective capture (`/mantle:retrospective` → `save-learning`) becomes a pure write. Observability-style commands should never mutate unrelated state.
- Terminal archival happens at the exact moment it semantically belongs: when the user approves the issue.
- Single archival site (the only existing caller) replaced by a single new archival site. No scatter.

## Does not

- Does not add a `--no-archive` flag to `save-learning`.
- Does not create a standalone `mantle archive-issue` CLI command.
- Does not change `core/archive.archive_issue` semantics or signature.
- Does not archive on `transition-to-verified` (would break the review-fail loopback).
- Does not migrate historical archive layout.
- Does not move learning files captured AFTER approval into `.mantle/archive/learnings/` — they live in `.mantle/learnings/` and are still found by `find_learning_path`.
- Does not change the retrospective prompt, state.md schema, or issue schema.
- Does not rewrite `implement.md` Step 9 beyond removing a workaround comment if one exists.