---
title: Research command (/mantle:research) with researcher agent
status: completed
slice:
- core
- claude-code
- agents
- vault
- tests
story_count: 3
verification: null
blocked_by: []
skills_required: []
tags:
- type/issue
- status/completed
acceptance_criteria:
- id: ac-01
  text: '`/mantle:research` is available in Claude Code and invokes the researcher
    subagent'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-02
  text: The researcher agent uses WebSearch and WebFetch to investigate the idea from
    multiple angles (feasibility, competitive, technology, user needs, risks)
  passes: false
  waived: false
  waiver_reason: null
- id: ac-03
  text: The researcher reads `.mantle/idea.md` for context and `.mantle/challenges/`
    transcripts if they exist
  passes: false
  waived: false
  waiver_reason: null
- id: ac-04
  text: Each research session produces a dated report in `.mantle/research/<date>-<focus>.md`
    with YAML frontmatter
  passes: false
  waived: false
  waiver_reason: null
- id: ac-05
  text: 'Research notes follow the schema: date, author, focus, confidence, idea_ref,
    tags, plus structured body sections'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-06
  text: The research note is stamped with `git config user.email`
  passes: false
  waived: false
  waiver_reason: null
- id: ac-07
  text: Multiple research rounds are supported — each produces a new dated file, not
    an overwrite
  passes: false
  waived: false
  waiver_reason: null
- id: ac-08
  text: 'State machine updated: `RESEARCH` status added with transitions from IDEA
    and CHALLENGE, and transition to PRODUCT_DESIGN'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-09
  text: '`mantle init` creates the `.mantle/research/` directory'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-10
  text: The researcher agent definition is installed to `~/.claude/agents/` via `mantle
    install`
  passes: false
  waived: false
  waiver_reason: null
- id: ac-11
  text: '`/mantle:help` updated to include `/mantle:research` in the "Idea & Validation"
    phase group'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-12
  text: Research is optional — design commands work without any research being run
  passes: false
  waived: false
  waiver_reason: null
- id: ac-13
  text: Tests verify research note format, frontmatter schema, state transitions,
    and retrieval
  passes: false
  waived: false
  waiver_reason: null
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

- [ ] ac-01: `/mantle:research` is available in Claude Code and invokes the researcher subagent
- [ ] ac-02: The researcher agent uses WebSearch and WebFetch to investigate the idea from multiple angles (feasibility, competitive, technology, user needs, risks)
- [ ] ac-03: The researcher reads `.mantle/idea.md` for context and `.mantle/challenges/` transcripts if they exist
- [ ] ac-04: Each research session produces a dated report in `.mantle/research/<date>-<focus>.md` with YAML frontmatter
- [ ] ac-05: Research notes follow the schema: date, author, focus, confidence, idea_ref, tags, plus structured body sections
- [ ] ac-06: The research note is stamped with `git config user.email`
- [ ] ac-07: Multiple research rounds are supported — each produces a new dated file, not an overwrite
- [ ] ac-08: State machine updated: `RESEARCH` status added with transitions from IDEA and CHALLENGE, and transition to PRODUCT_DESIGN
- [ ] ac-09: `mantle init` creates the `.mantle/research/` directory
- [ ] ac-10: The researcher agent definition is installed to `~/.claude/agents/` via `mantle install`
- [ ] ac-11: `/mantle:help` updated to include `/mantle:research` in the "Idea & Validation" phase group
- [ ] ac-12: Research is optional — design commands work without any research being run
- [ ] ac-13: Tests verify research note format, frontmatter schema, state transitions, and retrieval

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
