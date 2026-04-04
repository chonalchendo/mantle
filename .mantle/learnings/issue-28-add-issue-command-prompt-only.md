---
issue: 28
title: Add-issue command — prompt-only pipeline and status transition friction
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-04'
confidence_delta: '+2'
tags:
- type/learning
- phase/reviewing
---

## What Went Well

- **Build pipeline handles small issues cleanly**: The full build pipeline (shape → plan → implement → verify) ran end-to-end with zero retries, zero blocked stories, and all 8 acceptance criteria passing first try. For prompt-only issues where CLI infrastructure already exists, the pipeline completes in minutes.
- **Pattern reuse compounds**: Following brainstorm.md as the reference pattern for add-issue.md (same learning from issue 27) meant the implementing agent completed STATUS: DONE on first attempt. The sonnet model was sufficient for this single-file, pattern-following story.
- **Prompt-only approach was correct**: Shaping correctly identified that no Python code was needed — the existing `mantle save-issue` CLI handled all persistence. Approach B (core helper module) would have been pure over-engineering.

## Harder Than Expected

- **Status transitions still manual**: The review step had to chain `transition-issue-implementing → transition-issue-verified → transition-issue-approved` because the build pipeline doesn't auto-transition issue status as phases complete. Same friction as issue 27.

## Wrong Assumptions

- **None**: The shaped plan held exactly. Small batch appetite was accurate — single story, two files, no surprises.

## Recommendations

1. **Auto-transition issue status in build pipeline**: `build.md` should transition to `implementing` at Step 6, `verify.md` should transition to `verified` on pass. This eliminates the manual chaining in review. The state machine is correct — the automation is missing.
2. **Prompt-only issues are fast wins**: When CLI infrastructure exists, the build pipeline handles prompt-only commands with minimal overhead. Identify these early in shaping.
3. **Pattern reuse compounds across issues**: Always identify the reference module in story specs. Two consecutive issues (27, 28) had first-try agent completions by following established patterns.