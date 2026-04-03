---
title: Brainstorm command — validate new feature ideas against existing vision
status: planned
slice:
- claude-code
- core
story_count: 0
verification: null
blocked_by: []
tags:
- type/issue
- status/planned
---

## Parent PRD

product-design.md, system-design.md

## Why

After initial project setup, there is no lightweight pipeline for validating new feature ideas before they enter the backlog. The current workflow assumes ideas flow through the setup funnel (idea → challenge → design → plan-issues), but mid-project feature ideas have different needs: they must be evaluated against an existing vision, not from scratch. Without this, users either skip validation entirely (bad ideas enter the backlog) or have no entry point at all (good ideas get lost).

The key insight: product design is "stubborn on the vision" (the what/why doesn't change for individual features), while system design is "flexible on the details" (the how adapts). Brainstorm evaluates new ideas against the stubborn vision and either promotes them to the backlog or rejects them as scope creep.

## What to build

A `/mantle:brainstorm` command that helps users flesh out and validate feature ideas for existing projects. It combines structured exploration (from superpowers brainstorming) with selective challenge techniques (from /mantle:challenge) scaled to the idea's complexity.

### Flow

1. **Load context** — read product-design.md, system-design.md, existing issues, learnings
2. **Explore the idea** — conversational, one question at a time:
   - What problem does this solve for the target user?
   - How does this connect to the existing vision?
   - What's the non-obvious insight that makes this worth doing now?
3. **Vision alignment check** — the key differentiator:
   - Does this serve the stubborn vision in product-design.md?
   - Or is this scope creep / a distraction from more pressing work?
   - What existing issues would this complement or conflict with?
4. **Selective challenge** — apply challenge lenses (assumption surfacing, first-principles, devil's advocate, pre-mortem, competitive) based on what the idea needs. Small features get 3 exchanges; paradigm shifts get the full treatment. Read the room, don't follow a rigid checklist.
5. **Propose 2-3 lightweight approaches** — enough to understand appetite and feasibility, not full shaping.
6. **Verdict** — three outcomes:
   - **Proceed** → recommend `/mantle:add-issue`
   - **Research first** → recommend `/mantle:research` with specific questions
   - **Scrap** → explain why this doesn't serve the vision, suggest what to focus on instead

### Output

Saved to `.mantle/brainstorms/YYYY-MM-DD-<slug>.md` with structured sections (idea summary, vision alignment assessment, challenges explored, approaches considered, verdict). Scrapped ideas are preserved as valuable context ("we considered X and rejected it because Y").

### Design principles

- Explicit gate: brainstorm recommends next step but does not auto-transition
- Scale rigor to complexity: lightweight for small features, thorough for large ones
- Vision is the anchor: product-design.md is read but never suggested for modification
- One question per message, prefer multiple choice (from superpowers pattern)

## Acceptance criteria

- [ ] `/mantle:brainstorm` command exists as a Claude Code slash command
- [ ] Loads and references product-design.md, system-design.md, and existing issues
- [ ] Interactive conversational session (one question at a time)
- [ ] Vision alignment check explicitly evaluates idea against product design
- [ ] Selectively applies challenge lenses based on idea complexity
- [ ] Proposes 2-3 lightweight approaches with trade-offs
- [ ] Produces one of three verdicts: proceed, research first, or scrap
- [ ] Saves output to `.mantle/brainstorms/` with date-prefixed filename
- [ ] Scrapped ideas are saved (not discarded)
- [ ] Recommends next command based on verdict
- [ ] CLI support: `mantle save-brainstorm` command for persisting output

## Blocked by

None

## User stories addressed

- As a developer mid-project, I want to validate a new feature idea against my existing vision before adding it to the backlog, so that I don't pollute the backlog with scope creep
- As a developer, I want scrapped ideas recorded so that future brainstorms have context about what was already considered and why it was rejected