---
title: System design + decision logging (/mantle:design-system)
status: planned
slice: [core, claude-code, vault, tests]
story_count: 0
verification: null
tags:
  - type/issue
  - status/planned
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

- [ ] `/mantle:design-system` is available in Claude Code and starts an interactive system design session
- [ ] The session guides the user through architecture, tech choices, API contracts, and data model
- [ ] System design is saved as `.mantle/system-design.md` with YAML frontmatter
- [ ] Every decision made during the session is logged to `.mantle/decisions/<date>-<topic>.md`
- [ ] Decision log entries include rationale, alternatives considered, confidence level, reversibility, and reversal trigger
- [ ] `core/decisions.py` provides a clean interface for creating decision entries
- [ ] Project state transitions to "system-design"
- [ ] All notes are stamped with git identity
- [ ] Tests verify system design document structure, decision log entry format, and state transition

## Blocked by

- Blocked by issue-02 (needs `.mantle/` directory and vault.py)

## User stories addressed

- User story 13: Interactive session produces structured system design document
- User story 14: Every decision logged with rationale, alternatives, confidence, and reversal triggers
