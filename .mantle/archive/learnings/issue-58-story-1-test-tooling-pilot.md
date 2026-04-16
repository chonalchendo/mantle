---
issue: 58
title: 'story-1: test-tooling pilot'
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-16'
confidence_delta: '+0'
tags:
- type/learning
- phase/reviewing
---

## What went well

- Two external skills (inline-snapshot, dirty-equals) were created just-in-time and their references/core.md gave the implementer concrete patterns (named scenario fixture, IsPartialDict kwargs form) that shaped the story well.
- One vertical-slice story was the right sizing — all pilot concerns (deps, fixture, two migrations, docs) landed in a single coherent diff.

## Harder than expected

- inline-snapshot's `--inline-snapshot=create` formatter warning is noisy ("not able to format your code" suggests `inline-snapshot[black]`) — easy to mistake for a real failure. `just fix` (ruff) handles the formatting fine without the extra extra.
- `.mantle/` mantle-managed files (system-design.md, state.md, stories, sessions) got auto-committed by a mantle hook before the orchestrator's feat commit, producing a "chore(mantle): implement ..." commit intermixed with the feat commit. Not a problem but easy to confuse when reviewing history.

## Wrong assumptions

- Story spec used dict-literal form `IsPartialDict({...})` — implementer used kwargs form `IsPartialDict(issue=21, ...)`, which is equally correct and more readable. Story specs should treat library example code as a starting point, not canonical.

## Recommendations

- When adding snapshot testing libraries to a project, mention in the adoption PR that `--inline-snapshot=review` is the preferred workflow (TUI-driven accept/reject) over `create` for incremental work.
- For future dirty-equals migrations, prefer kwargs form for IsPartialDict when the dict literal would be a stable field list — reads as a spec not a data structure.