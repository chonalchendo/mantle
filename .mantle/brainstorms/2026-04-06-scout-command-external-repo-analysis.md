---
date: '2026-04-06'
author: 110059232+chonalchendo@users.noreply.github.com
title: scout-command-external-repo-analysis
verdict: proceed
tags:
- type/brainstorm
---

## Brainstorm Summary

**Idea**: Scout command — external repo analysis with project context
**Problem**: Users frequently clone external repos to learn from them, but ad hoc analysis prompts miss the rich context Mantle already has (product design, system design, backlog, skills). Findings are unstructured and not persisted.
**Vision alignment**: Strong — extends the knowledge engine pillar with external intelligence. Compiled context (design principle #3) becomes the analysis lens. AI surfaces insights, human decides what to port (design principle #4).

## Exploration

**Problem framing**: The user repeatedly runs loose prompts asking Claude to clone repos and analyze them. The analysis would be significantly more useful if it was guided by the projects product vision, system design, current backlog gaps, and accumulated learnings — all of which Mantle already has.

**Key insight**: Mantle already compiles internal context for implementation and planning. Using that same compiled context as a lens for external codebase analysis is a natural extension — not a new capability, but a new application of existing infrastructure.

**Scope**: Medium capability (1-2 issues). Parallel agent orchestrator modeled on /mantle:research with vision-alignment lens from /mantle:brainstorm.

## Challenges Explored

**Assumption surfacing** (3 assumptions, medium depth):

1. "The analysis is useful enough to persist" — HELD. User already does this frequently and acts on findings. Structured output with vision alignment would increase signal-to-noise.
2. "Product/system design is the right lens" — HELD. The whole point is that ad hoc analysis misses this context. Injecting design docs produces targeted "whats relevant to your project" analysis rather than generic observations.
3. "One repo at a time is the right unit" — SCOPED DOWN. Cross-repo comparison is attractive but not the primary workflow. Single-repo first, output format should support future cross-repo synthesis.

**Devils advocate**: Challenged whether this is a general feature or personal workflow. User cited external validation — others on Twitter describe this as a favourite AI workflow. General enough for first-class command status.

**Output destination**: Challenged reports/ vs .mantle/ integration. Settled on .mantle/scouts/ — integrates with knowledge engine primitives so findings can be surfaced by /mantle:query and referenced during /mantle:shape-issue.

## Approaches Considered

| Approach | Description | Key Trade-off |
|----------|-------------|---------------|
| A: Prompt-only | Single .claude/commands/ prompt, no Python runtime | Ships fast but no cleanup, no CLI state management |
| B: CLI-assisted prompt | mantle scout url handles clone/cleanup, prompt handles analysis | Clean separation but medium scope |
| C: Agent-spawning orchestrator | Parallel sub-agents for different analysis dimensions, like /mantle:research | Deepest analysis, highest scope. Modeled on proven patterns |

## Verdict

**Verdict**: proceed
**Reasoning**: Strong vision alignment, proven user need (frequent ad hoc usage), and existing patterns to build on (/mantle:research for orchestration, /mantle:brainstorm for vision-alignment lens). The command formalizes something users already do and makes it significantly better by injecting compiled project context.
**If proceeding**: Create issue covering: (1) CLI mantle scout repo-url for clone/cleanup, (2) prompt orchestrator that compiles product design + system design + backlog + learnings as analysis lens, (3) parallel agents for architecture, patterns, testing, CLI design dimensions, (4) structured report saved to .mantle/scouts/ via mantle save-scout, (5) integration with knowledge engine so reports are queryable. Name: /mantle:scout. Design output format to support future cross-repo synthesis without rearchitecting.