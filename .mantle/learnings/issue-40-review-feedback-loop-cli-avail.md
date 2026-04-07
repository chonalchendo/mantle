---
issue: 40
title: Review feedback loop — CLI availability gap, false blockers
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-07'
confidence_delta: '+0'
tags:
- type/learning
- phase/reviewing
---

## What Went Well

- **Correct approach selection**: Shaping chose minimal approach (save/load + fix.md) over full build integration. Small batch appetite was accurate — 2 stories, clean pipeline.
- **Model reuse**: Existing ReviewChecklist and ReviewItem models needed no changes. save_review_result just added persistence on top of existing data structures.
- **Clean pipeline**: Build → simplify → verify → review all passed first try. No blocked stories, no retries.

## Harder Than Expected

- **CLI availability gap**: New CLI commands (save-review-result, load-review-result) were committed to source but aren't available at runtime until the next release. The review.md prompt now references commands that don't exist in the installed package. This means the full review-fix loop won't work until a release is cut.

## Wrong Assumptions

- **False blocker on issue 37**: Issue 40 listed issue-37 (backward status transitions) as a blocker, but the implemented → implementing transition was already in the codebase. The blocker was stale — issue 37 had already been completed.

## Recommendations

1. **Check blocker status before building**: When an issue lists blocked_by, verify the blocker's actual status before treating it as blocked. Issues can be completed without their status being updated in dependent issues.
2. **Account for CLI availability lag**: When an issue adds new CLI commands that prompts reference, note that the commands won't be available until the next release. Consider whether a release should be cut before the issue is truly "done" from a user perspective.
3. **Extending existing models with persistence is cheap**: When core data models already exist (like ReviewChecklist), adding save/load is a well-trodden pattern. Shape these as small batch confidently.