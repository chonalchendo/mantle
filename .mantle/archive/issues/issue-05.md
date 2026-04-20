---
title: Product design (/mantle:design-product)
status: completed
slice:
- core
- claude-code
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
  text: '`/mantle:design-product` is available in Claude Code and starts an interactive
    product design session'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-02
  text: The session guides the user through features, target users, success metrics,
    and genuine edge
  passes: false
  waived: false
  waiver_reason: null
- id: ac-03
  text: Product design is saved as `.mantle/product-design.md` with YAML frontmatter
  passes: false
  waived: false
  waiver_reason: null
- id: ac-04
  text: Project state transitions to "product-design"
  passes: false
  waived: false
  waiver_reason: null
- id: ac-05
  text: The note is stamped with git identity and timestamps
  passes: false
  waived: false
  waiver_reason: null
- id: ac-06
  text: Tests verify document structure, frontmatter, and state transition
  passes: false
  waived: false
  waiver_reason: null
---

## Parent PRD

product-design.md, system-design.md

## What to build

The `/mantle:design-product` Claude Code command that runs an interactive session defining the "what and why" of the product — features, target users, success metrics, and genuine edge. The session produces `.mantle/product-design.md` as a structured document and updates project state.

This includes:
- `claude/commands/mantle/design-product.md` — static command prompt guiding structured product design
- `vault-templates/product-design.md` — Obsidian note template for product design
- Integration with `core/vault.py` for document creation and `core/state.py` for state transition to "product-design"

## Acceptance criteria

- [ ] ac-01: `/mantle:design-product` is available in Claude Code and starts an interactive product design session
- [ ] ac-02: The session guides the user through features, target users, success metrics, and genuine edge
- [ ] ac-03: Product design is saved as `.mantle/product-design.md` with YAML frontmatter
- [ ] ac-04: Project state transitions to "product-design"
- [ ] ac-05: The note is stamped with git identity and timestamps
- [ ] ac-06: Tests verify document structure, frontmatter, and state transition

## Blocked by

- Blocked by issue-02 (needs `.mantle/` directory and vault.py)

## User stories addressed

- User story 12: Interactive session produces structured product design document
