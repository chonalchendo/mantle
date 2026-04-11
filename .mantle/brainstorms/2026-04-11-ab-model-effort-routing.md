---
date: '2026-04-11'
author: 110059232+chonalchendo@users.noreply.github.com
title: ab-model-effort-routing
verdict: research
tags:
- type/brainstorm
---

## Brainstorm Summary

**Idea**: A/B model/effort strategy across build pipeline stages
**Problem**: Build pipeline may be over-spending tokens and time by using the most capable model for every story, when simpler stories could use cheaper/faster models.
**Vision alignment**: Moderate — optimises an existing pipeline stage rather than adding a core workflow capability, but makes sustained use more practical.

## Exploration

**What**: Route each story in the implement orchestrator to the cheapest model that can handle it, based on structured story metadata (file count, slice, test-only flag, complexity from shaping). Oh-my-claudecode does this with keyword heuristics; Mantle has richer structured metadata for more accurate routing.

**Non-obvious insight**: Better scoped stories (from skill injection, standardised anatomy — issues 51-53) would give routing heuristics stronger signals. The model can be cheaper because the prompt does more heavy lifting. This idea gets more valuable after the context management issues are implemented.

**Size**: Medium capability (1 issue, 3-4 stories).

## Challenges Explored

**Assumption surfacing**: Three assumptions identified — (1) metadata reliably predicts model requirements, (2) quality difference is small for simple stories, (3) savings are material. User least confident about 1 and 2.

**First-principles**: Having Opus label model requirements during planning is circular — difficulty often reveals itself during implementation, not before. A story routed to Sonnet that fails both retries costs more than Opus first-try.

**Devil's advocate — key finding**: Model routing already exists in implement.md. The orchestrator has explicit guidance to use Sonnet for simple stories and Opus for complex ones. The story-implementer agent defaults to Opus. The user wasn't aware this existed. The real gap is not routing logic — it's that there's no visibility into whether the existing routing is being followed or where time/tokens are actually spent.

## Approaches Considered

| Approach | Description | Key Trade-off |
|----------|-------------|---------------|
| Measure first | Add build logging — model used, pass/fail, retry outcome per story | Data without immediate savings; small appetite |
| Explicit model tags | plan-stories writes model_hint into story metadata | Reviewable decisions but planning-time judgment may not match reality; medium appetite |
| Tighten existing guidance | Sharpen implement.md routing criteria, manually verify compliance | Zero code but relies on prompt compliance; trivial appetite |

## Verdict

**Verdict**: research
**Reasoning**: The brainstorm revealed that model routing already exists in implement.md but there's no observability into whether it's working. Building smarter routing without baseline data is premature optimisation. The prerequisite is measurement — knowing which models are used per story, pass/fail rates, and where time is spent. Additionally, the context management issues (51-53) should land first, as better-scoped stories with richer metadata would make any future routing more effective.
**If researching**: (1) What build telemetry can be captured without modifying core — just prompt/orchestrator changes? (2) Can Claude Code's existing session data provide model usage info? (3) What's the minimum viable build log format that would inform routing decisions? (4) After 5-10 builds with logging, is there actually a meaningful cost/speed gap between the current approach and optimal routing?