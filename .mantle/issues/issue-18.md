---
title: Research command (/mantle:research) with researcher agent
status: completed
slice: [core, claude-code, agents, vault, tests]
story_count: 3
verification: null
tags:
  - type/issue
  - status/completed
---

## Parent PRD

product-design.md, system-design.md

## What to build

The `/mantle:research` Claude Code command that invokes a researcher subagent to validate whether a user's idea can be implemented. The researcher uses web search and web fetch to investigate technical feasibility, existing solutions, competitive landscape, technology options, user needs, and risks — then produces a structured research report saved to `.mantle/research/`.

Research sits in the workflow after Challenge and before Design. It is optional (like challenge) but critical for validating that an idea is technically sound before committing to a design. Multiple research rounds are supported — each session produces a dated report in `.mantle/research/`, allowing iterative investigation from different angles.

This includes:

- `claude/commands/mantle/research.md` — static command prompt that triggers the researcher agent with project context (idea, challenge transcripts if available)
- `claude/agents/researcher.md` — researcher subagent definition that uses WebSearch and WebFetch to investigate the idea from all angles and produce a structured report
- `src/mantle/core/research.py` — research note schema (Pydantic frontmatter), creation, and retrieval functions
- `vault-templates/research.md` — Obsidian note template for research reports
- State machine update: add `RESEARCH` status with transitions `IDEA → RESEARCH`, `CHALLENGE → RESEARCH`, `RESEARCH → PRODUCT_DESIGN`
- `.mantle/research/` directory created during `mantle init`

### Research angles (adaptive, not a rigid checklist)

The researcher agent weaves through these angles based on the idea and conversation flow:

1. **Technical feasibility** — Can this be built? What APIs, libraries, or platform capabilities exist? What are the hard technical constraints or blockers?
2. **Existing solutions** — What's already out there? How do they work? What are their strengths and gaps?
3. **Technology options** — What tools, frameworks, or services could be used? What are the tradeoffs?
4. **User needs** — What do users in this space actually want? What problems are they reporting?
5. **Risks and unknowns** — What could go wrong? What assumptions need validation? What's the biggest unknown?

### Research report schema

```yaml
---
date: 2026-02-24
author: conal@company.com
focus: general | feasibility | competitive | technology | user-needs
confidence: 7/10
idea_ref: idea.md
tags:
  - type/research
  - phase/research
---

## Summary
One-paragraph synthesis of findings.

## Key Findings
- Finding 1 with source
- Finding 2 with source

## Feasibility Assessment
Can this be built? What exists to support it?

## Existing Solutions
What's already out there and how does this idea differ?

## Technology Options
Recommended technologies with tradeoffs.

## Risks & Unknowns
What needs further investigation?

## Recommendation
Go / pivot / investigate further — with rationale.
```

## Acceptance criteria

- [ ] `/mantle:research` is available in Claude Code and invokes the researcher subagent
- [ ] The researcher agent uses WebSearch and WebFetch to investigate the idea from multiple angles (feasibility, competitive, technology, user needs, risks)
- [ ] The researcher reads `.mantle/idea.md` for context and `.mantle/challenges/` transcripts if they exist
- [ ] Each research session produces a dated report in `.mantle/research/<date>-<focus>.md` with YAML frontmatter
- [ ] Research notes follow the schema: date, author, focus, confidence, idea_ref, tags, plus structured body sections
- [ ] The research note is stamped with `git config user.email`
- [ ] Multiple research rounds are supported — each produces a new dated file, not an overwrite
- [ ] State machine updated: `RESEARCH` status added with transitions from IDEA and CHALLENGE, and transition to PRODUCT_DESIGN
- [ ] `mantle init` creates the `.mantle/research/` directory
- [ ] The researcher agent definition is installed to `~/.claude/agents/` via `mantle install`
- [ ] `/mantle:help` updated to include `/mantle:research` in the "Idea & Validation" phase group
- [ ] Research is optional — design commands work without any research being run
- [ ] Tests verify research note format, frontmatter schema, state transitions, and retrieval

## Blocked by

- Blocked by issue-02 (needs `.mantle/` directory, vault.py, and state.py)
- Ideally implemented after issue-03 (idea capture) and issue-04 (challenge), since the researcher reads their outputs as context

## User stories addressed

_New user stories (not in original PRD — extends the workflow):_

- As a developer, I want to run `/mantle:research` and have an AI agent investigate whether my idea is technically feasible by searching the web for relevant APIs, libraries, and existing solutions, so that I validate feasibility before investing in design.
- As a developer, I want research reports saved as dated markdown files in `.mantle/research/` with structured metadata, so that findings accumulate over multiple sessions and feed into the design phase.
- As a developer, I want to run multiple research sessions focusing on different angles (feasibility, competitive landscape, technology options), so that I can investigate incrementally rather than trying to cover everything at once.
- As a developer, I want the research phase to be optional, so that I can skip it when I already know the landscape or am building something straightforward.
- As a developer, I want my design sessions to have access to research findings as context, so that product and system design decisions are grounded in evidence rather than assumptions.
