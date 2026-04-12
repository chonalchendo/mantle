---
title: Build pipeline observability — per-story model and performance telemetry
status: approved
slice:
- cli
- core
story_count: 2
verification: null
blocked_by: []
skills_required:
- Design Review
- DuckDB Best Practices and Optimisations
- DuckLake
- Howard Marks Investment Philosophy
- John Templeton Investment Philosophy
- Mohnish Pabrai Investment Philosophy
- OpenRouter LLM Gateway
- Python 3.14
- Python package structure
- SQLMesh Best Practices
- Tom Gayner Investment Philosophy
- cyclopts
- omegaconf
- pydantic-discriminated-unions
- pydantic-project-conventions
tags:
- type/issue
- status/approved
---

## Problem

The implement orchestrator already routes stories to different models (Opus for complex, Sonnet for simple) via guidance in implement.md, but there is no visibility into whether this routing is being followed or where time and tokens are actually spent. Without baseline data, any optimisation (smarter routing, model downgrading, effort tuning) is guesswork.

## Goal

Add lightweight telemetry to the build pipeline so that after each `/mantle:build` or `/mantle:implement` run, the user can see: which model was used per story, pass/fail on first attempt, retry outcomes, and relative duration. This data informs whether the existing routing works and where the actual bottlenecks are.

## Acceptance Criteria

- [ ] Each story implementation records: model used, first-attempt pass/fail, retry outcome (if any)
- [ ] Build summary is saved to a structured file (e.g., `.mantle/builds/` or story metadata)
- [ ] User can review build performance after a run without digging through session logs
- [ ] No changes to the routing logic itself — this is measurement only

## Prerequisites

**Research required before shaping.** This issue emerged from the [A/B model/effort routing brainstorm](../brainstorms/2026-04-11-ab-model-effort-routing.md) which identified observability as the prerequisite to any routing optimisation. Before shaping, run `/mantle:research` to investigate:

1. Can Claude Code session data already provide model usage info without custom logging?
2. What's the minimum viable build log format that would inform future routing decisions?
3. Where in the implement orchestrator can telemetry be captured — prompt-level changes vs core module changes?
4. How does Colin's cost attribution manifest work and is any of that pattern transferable?

## Context

- Model routing guidance already exists in `implement.md` (Opus default, Sonnet for simple stories)
- The story-implementer agent definition sets `model: opus`
- Issues 51-53 (context management) should land first — better-scoped stories make future routing optimisation more effective
- This issue is measurement only; a follow-up issue for smarter routing would depend on findings here

## Depends On

None strictly, but best sequenced after issues 51-53 (context management improvements).