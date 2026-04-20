---
title: System design + decision logging (/mantle:design-system)
status: completed
slice:
- core
- claude-code
- vault
- tests
story_count: 0
verification: null
blocked_by: []
skills_required: []
tags:
- type/issue
- status/completed
acceptance_criteria:
- id: ac-01
  text: '`/mantle:design-system` is available in Claude Code and starts an interactive
    system design session'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-02
  text: The session guides the user through architecture, tech choices, API contracts,
    and data model
  passes: false
  waived: false
  waiver_reason: null
- id: ac-03
  text: System design is saved as `.mantle/system-design.md` with YAML frontmatter
  passes: false
  waived: false
  waiver_reason: null
- id: ac-04
  text: Every decision made during the session is logged to `.mantle/decisions/<date>-<topic>.md`
  passes: false
  waived: false
  waiver_reason: null
- id: ac-05
  text: Decision log entries include rationale, alternatives considered, confidence
    level, reversibility, and reversal trigger
  passes: false
  waived: false
  waiver_reason: null
- id: ac-06
  text: '`core/decisions.py` provides a clean interface for creating decision entries'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-07
  text: Project state transitions to "system-design"
  passes: false
  waived: false
  waiver_reason: null
- id: ac-08
  text: All notes are stamped with git identity
  passes: false
  waived: false
  waiver_reason: null
- id: ac-09
  text: Tests verify system design document structure, decision log entry format,
    and state transition
  passes: false
  waived: false
  waiver_reason: null
---

## Parent PRD

product-design.md, system-design.md

## What to build

The `/mantle:design-system` Claude Code command that runs an interactive session defining the "how" — architecture, tech choices, API contracts, data model. Every decision made during the session is automatically logged to `.mantle/decisions/` with rationale, alternatives, confidence, and reversal triggers. System design should be approached from first principles, asking the fundamental question: what are the core building blocks of this project that we need to nit together into a production system? The project folder structure should reflect the first principles design.

This includes:
- `claude/commands/mantle/design-system.md` — static command prompt guiding structured system design with decision logging instructions
- `vault-templates/system-design.md` — Obsidian note template for system design
- `vault-templates/decision.md` — Obsidian note template for decision log entries
- `src/mantle/core/decisions.py` — create decision log entries with structured metadata (date, author, topic, confidence, reversibility, alternatives, rationale, reversal trigger)
- Integration with `core/vault.py` and `core/state.py` for document creation and state transition to "system-design"

## Acceptance criteria

- [ ] ac-01: `/mantle:design-system` is available in Claude Code and starts an interactive system design session
- [ ] ac-02: The session guides the user through architecture, tech choices, API contracts, and data model
- [ ] ac-03: System design is saved as `.mantle/system-design.md` with YAML frontmatter
- [ ] ac-04: Every decision made during the session is logged to `.mantle/decisions/<date>-<topic>.md`
- [ ] ac-05: Decision log entries include rationale, alternatives considered, confidence level, reversibility, and reversal trigger
- [ ] ac-06: `core/decisions.py` provides a clean interface for creating decision entries
- [ ] ac-07: Project state transitions to "system-design"
- [ ] ac-08: All notes are stamped with git identity
- [ ] ac-09: Tests verify system design document structure, decision log entry format, and state transition

## Blocked by

- Blocked by issue-02 (needs `.mantle/` directory and vault.py)

## User stories addressed

- User story 13: Interactive session produces structured system design document
- User story 14: Every decision logged with rationale, alternatives, confidence, and reversal triggers
