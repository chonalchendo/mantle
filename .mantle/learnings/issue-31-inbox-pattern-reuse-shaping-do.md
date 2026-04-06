---
issue: 31
title: Inbox — pattern reuse, shaping does-not gap, status transition debt
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-06'
confidence_delta: '+1'
tags:
- type/learning
- phase/reviewing
---

## What Went Well

- **Fifth consecutive clean build**: Zero blocked stories, zero retries. Build pipeline reliability confirmed across issues 27, 28, 30, 33, 31.
- **Shaped plan held**: Bug-Pattern Lite was the right call. Core module, CLI, and prompts all followed established patterns with no surprises. Small batch appetite accurate.
- **Pattern reuse compounding**: Story agents completed first-try by following bugs.py (core) and cli/bugs.py (CLI). Three consecutive issues with first-try agent completions.
- **Code review caught real quality issues**: Dead code, missing edge-case tests, testing-private-function anti-pattern — all caught and fixed in one pass.

## Harder Than Expected

- **Verification caught an AC gap**: AC 5 (build pipeline reports AI-suggested ideas) was not covered by any story. The shaping "Does not" section explicitly excluded build.md changes, but the AC required them. Fixed inline during verification.
- **Issue status transitions still manual**: Same friction as issues 27, 28, 33. Had to chain transition-issue-implementing → transition-issue-verified → transition-issue-approved during review.
- **Broken session log frontmatter**: Pre-existing session log missing required fields blocked mantle compile. Had to fix manually.

## Wrong Assumptions

- **Shaping "Does not" contradicted AC 5**: The shaped issue said "does not modify build.md prompts" but AC 5 required exactly that. The "Does not" section was derived from architecture boundaries without cross-checking against acceptance criteria.

## Recommendations

1. **Cross-check "Does not" against ACs during shaping**: Every AC must map to at least one story. If a "Does not" item contradicts an AC, that's a shaping bug. Add this as a validation step in shape-issue.md.
2. **Auto-transition issue status in build pipeline**: Five issues with the same manual-transition friction. build.md should transition to implementing at Step 6; verify should transition on pass. This is the most-repeated recommendation across retrospectives.
3. **Graceful session log validation**: mantle compile fails hard on invalid frontmatter. Consider skipping invalid logs with a warning rather than blocking compilation entirely.