---
title: Design revision (/mantle:revise-product + /mantle:revise-system)
status: planned
slice: [core, claude-code, tests]
story_count: 0
verification: null
tags:
  - type/issue
  - status/planned
---

## Parent PRD

product-design.md, system-design.md

## What to build

Separate commands for revising existing product and system designs. Each command reads the current design document, opens an interactive revision session, updates the document, and automatically creates a decision log entry capturing what changed and why. Keeps create and update concerns separate for optimal AI output (one command, one job).

This includes:
- `claude/commands/mantle/revise-product.md` — static command that reads current product design and guides revision
- `claude/commands/mantle/revise-system.md` — static command that reads current system design and guides revision
- Integration with `core/decisions.py` to auto-create decision log entries on every revision

## Acceptance criteria

- [ ] `/mantle:revise-product` reads the current `.mantle/product-design.md` and opens an interactive revision session
- [ ] `/mantle:revise-system` reads the current `.mantle/system-design.md` and opens an interactive revision session
- [ ] Each revision automatically creates a decision log entry in `.mantle/decisions/` capturing what changed and why
- [ ] Decision log entries reference the revised document and include before/after summary
- [ ] Commands error clearly if the design document doesn't exist yet (directs user to create command)
- [ ] Tests verify revision flow, decision log creation, and error handling for missing documents

## Blocked by

- Blocked by issue-05 (needs product design to revise)
- Blocked by issue-06 (needs system design to revise, plus decisions.py)

## User stories addressed

- User story 15: Revise product design in interactive session
- User story 16: Revise system design in interactive session
- User story 17: Every revision creates a decision log entry
