---
title: Collapse per-story code review into simplify step
status: verified
slice:
- claude-code
story_count: 3
verification: null
blocked_by: []
skills_required:
- CLI design best practices
- Design Review
- EarningsCall.biz Scraping
- Python 3.14
- docker-compose-python
- omegaconf
- pydantic-discriminated-unions
tags:
- type/issue
- status/verified
---

## Parent PRD

product-design.md, system-design.md

## Why

The build pipeline runs two overlapping quality checks: a per-story code-reviewer agent (implement.md step 7) and a post-implementation simplify step (build.md step 7). Five of the eight bloat patterns in the simplify checklist overlap with what the code reviewer checks. The per-story review runs N times (once per story), most invocations return PASS, and it misses the cross-story patterns that actually need a separate pass. TDD already covers spec compliance. This wastes tokens, time, and creates conceptual messiness with two sources for code quality review.

## What to build

Remove the per-story code-reviewer from the implementation loop and make the simplify step the single quality gate. Update the simplify skip condition to use a composite heuristic (file count + lines changed) instead of the current file-count-only threshold.

### Flow

1. Implementation loop runs stories as before (implement, test, retry on failure)
2. Per-story code-reviewer step (implement.md step 7) is removed — after tests pass, proceed directly to commit
3. After all stories complete, the build pipeline evaluates the skip condition using `git diff --stat` (file count + lines added)
4. If changes exceed the threshold, the simplify step runs as the single quality gate
5. If changes are below the threshold, simplification is skipped

## Acceptance criteria

- [ ] Per-story code-reviewer agent spawn removed from implement.md (step 7 and its fix cycle)
- [ ] Build pipeline skip condition uses composite heuristic: file count AND lines changed (not file count alone)
- [ ] Simplify checklist unchanged — no code review checks absorbed
- [ ] Standalone `/mantle:simplify` continues to work independently of the build pipeline
- [ ] A build run with a small issue (few files, few lines) skips simplification
- [ ] A build run with a large issue (many files or many lines) triggers simplification

## Brainstorm reference

.mantle/brainstorms/2026-04-11-collapse-code-review-into-simplify.md

## Blocked by

None

## User stories addressed

- As a developer, I want the build pipeline to have a single, focused quality gate so that token spend and build time are minimised without sacrificing code quality
- As a developer, I want the simplify skip condition to consider lines changed (not just file count) so that large changes in few files still get reviewed