---
issue: 39
title: Document verify vs review distinction — prompt-only pattern
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-07'
confidence_delta: '+0'
tags:
- type/learning
- phase/reviewing
---

## What Went Well

- **Prompt-only approach validated**: Shaping correctly identified that no Python code was needed — the convention check works as an AI-driven review step within the verify prompt. Smallest-appetite approach satisfied all 4 acceptance criteria.
- **Single-story decomposition**: A 2-file prompt edit doesn't need multiple stories. One story covering all ACs kept the pipeline efficient with zero overhead.
- **Clean pipeline run**: Build → verify → review passed end-to-end with no blockers, no retries, no review issues.

## Harder Than Expected

- Nothing — routine prompt edit as anticipated.

## Wrong Assumptions

- None.

## Recommendations

1. **Prompt-only issues are a validated pattern**: When an issue only changes command prompts (no Python code), shape as prompt-only with a single story. The build pipeline handles these cleanly.
2. **Step numbering convention**: Using decimal step numbers (e.g. Step 6.5) to insert between existing steps avoids renumbering and breaking references in other orchestrators like build.md. Use this pattern for future prompt insertions.