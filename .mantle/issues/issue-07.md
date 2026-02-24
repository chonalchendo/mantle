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

### Vision section enforcement

Both design documents have a `## Vision` section at the very top (5-10 lines max) that serves as a north-star compass. After any revision to the document body, the revise commands check whether the Vision section still reflects the change. If not, the AI updates it as part of the same revision. This ensures the concise summary never drifts from the detailed spec — one file, one source of truth, with the top section always glanceable.

This includes:
- `claude/commands/mantle/revise-product.md` — static command that reads current product design and guides revision
- `claude/commands/mantle/revise-system.md` — static command that reads current system design and guides revision
- Integration with `core/decisions.py` to auto-create decision log entries on every revision

## Acceptance criteria

- [ ] `/mantle:revise-product` reads the current `.mantle/product-design.md` and opens an interactive revision session
- [ ] `/mantle:revise-system` reads the current `.mantle/system-design.md` and opens an interactive revision session
- [ ] Each revision automatically creates a decision log entry in `.mantle/decisions/` capturing what changed and why
- [ ] Decision log entries reference the revised document and include before/after summary
- [ ] After each revision, the `## Vision` section is checked and updated if it no longer reflects the change
- [ ] Commands error clearly if the design document doesn't exist yet (directs user to create command)
- [ ] Tests verify revision flow, decision log creation, Vision sync, and error handling for missing documents

## Blocked by

- Blocked by issue-05 (needs product design to revise)
- Blocked by issue-06 (needs system design to revise, plus decisions.py)

## User stories addressed

- User story 15: Revise product design in interactive session
- User story 16: Revise system design in interactive session
- User story 17: Every revision creates a decision log entry
