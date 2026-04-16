---
issue: 46
title: save-learning-archive-decoupling
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-10'
confidence_delta: '+1'
tags:
- type/learning
- phase/reviewing
---

## What went well

- **Live E2E test during review** was the most valuable quality gate this issue. Unit tests all passed, but running the real `mantle save-learning` CLI against a throwaway mid-pipeline fixture in `/tmp/` caught the review.md ordering regression that no unit test covered. Recommend making this a standard review practice: build a throwaway fixture, run the real CLI, inspect the filesystem.
- Shape accuracy was high — approach (a) was correctly predicted as cleanest, the import-cycle rabbit hole was anticipated and handled (archive call lives in CLI wrapper, not core), and single-story sizing was right for tightly-coupled work across two CLI files.

## Harder than expected

- **Review.md ordering regression**: moving archival from `save-learning` to `transition-to-approved` broke `save-review-result`, which runs AFTER approval in review.md's documented flow. `find_issue_path` only reads `.mantle/issues/`, so it can't find the just-archived issue. Required a prompt-file fix (swap steps 1 and 2 in review.md's approved branch) before the release was consistent.
- **Installed-vs-working-tree CLI divergence**: the installed `mantle` at `~/.local/bin/mantle` was v0.11.0 (pre-fix). Any mid-pipeline call to `mantle save-learning` from `implement.md` Step 9 would re-trigger the bug. Had to skip extract-learnings entirely during the build and cut a release before the fix was usable end-to-end.

## Wrong assumptions

- **Issue text assumed transition-to-verified was the archival point**. Wrong — `verified → implementing` is an allowed rollback transition for failed reviews. `approved` is the only truly terminal state. Shaping caught this before implementation, so no wasted effort, but authors' first instinct on transition semantics can be wrong.
- **Nobody anticipated that moving archival would break a downstream command**. The shape doc's 'Does not' section was thorough about what wouldn't change but didn't trace ordering dependencies in the CLI prompt flow after the new side effect.

## Recommendations

1. **Always run a live E2E test during review** — not just unit tests. Build a throwaway fixture, run the real CLI, inspect the filesystem. This catches prompt-flow regressions and ordering bugs that unit tests can't see.
2. **When moving a side effect, trace all downstream dependents of the new call site.** Add a 'side-effect impact scan' to shaping: list every command and prompt that runs after the new side effect fires. Would have surfaced the review.md ordering issue pre-implementation.
3. **Account for installed-vs-working-tree CLI divergence when fixing CLI bugs.** If the fix changes `mantle` CLI behaviour, the installed version won't pick it up until a release. Shape docs for CLI bugs should note whether extract-learnings or other mid-pipeline CLI calls need to be skipped during this specific build run.