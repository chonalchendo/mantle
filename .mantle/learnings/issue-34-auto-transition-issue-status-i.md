---
issue: 34
title: Auto-transition issue status — idempotent CLI pattern
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-06'
confidence_delta: '+1'
tags:
- type/learning
- phase/reviewing
---

## What went well

- The shaped approach (prompt + minimal core wiring) held up exactly — small batch was accurate.
- The full /mantle:build pipeline worked smoothly for a small, well-scoped issue.
- Extending the existing `transition_to_*` pattern required minimal new code.
- Simplification step caught real duplication in cli/review.py and produced a cleaner shared helper.

## Harder than expected

Nothing — plan held up cleanly.

## Recommendations

- **Idempotent transitions are a reusable pattern.** Adding the current status as an allowed source in `_ALLOWED_TRANSITIONS` (e.g., `implementing -> implementing`) makes CLI commands safe to call from multiple pipeline entry points without pre-checking current state. Future pipeline-called commands should follow this pattern.
- **The build pipeline is well-suited for small-batch issues.** The 9-step flow felt proportionate for this scope. No steps felt wasted.