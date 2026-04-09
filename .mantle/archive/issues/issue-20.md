---
title: Bug capture (/mantle:bug)
status: completed
slice: [core, claude-code, vault, tests]
story_count: 3
verification: null
tags:
  - type/issue
  - status/planned
---

## Parent PRD

product-design.md, system-design.md

## What to build

The `/mantle:bug` Claude Code command for quick bug capture during a session. When a developer discovers a bug — during testing, implementation, or general use — they run `/mantle:bug` and the AI guides a brief structured capture. The bug is saved to `.mantle/bugs/` with metadata and reproduction context.

Bugs feed into the planning workflow. When running `/mantle:plan-issues`, the command reads `.mantle/bugs/` and surfaces unfixed bugs as candidates for new issues. A bug becomes an issue when the user decides to act on it — until then it's a lightweight log entry, not a commitment.

This mirrors the idea capture pattern: `/mantle:idea` captures ideas that flow into design, `/mantle:bug` captures bugs that flow into planning.

This includes:

- `claude/commands/mantle/bug.md` — static command prompt that guides structured bug capture
- `src/mantle/core/bugs.py` — bug note schema (Pydantic frontmatter), creation, listing, and retrieval
- `vault-templates/bug.md` — Obsidian note template for bug reports
- `.mantle/bugs/` directory created during `mantle init`
- Integration with `/mantle:plan-issues` — surfaces open bugs as issue candidates

### Bug capture flow

The command guides a brief interactive capture:

1. **What happened?** — One-line summary
2. **How to reproduce** — Steps or context (the AI can infer from the current session if the bug was just encountered)
3. **Expected vs actual** — What should have happened
4. **Severity** — blocker / high / medium / low (AI suggests based on description, user confirms)
5. **Related context** — Which issue/story was being worked on, relevant files

The capture should be fast — 30 seconds for a simple bug, not a ceremony.

### Bug report schema

```yaml
---
date: 2026-02-25
author: conal@company.com
summary: Compilation fails when no idea.md exists
severity: medium | high | low | blocker
status: open | fixed | wont-fix
related_issue: issue-08  # optional
related_files:
  - src/mantle/core/compiler.py
fixed_by: issue-21  # populated when resolved via an issue
tags:
  - type/bug
  - severity/medium
  - status/open
---

## Description
One-paragraph description of the bug.

## Reproduction
Steps or context to reproduce.

## Expected Behaviour
What should happen.

## Actual Behaviour
What actually happens.
```

### Integration with planning

`/mantle:plan-issues` gains awareness of `.mantle/bugs/`:
- At the start of a planning session, surfaces open bugs: "There are 3 open bugs. Want to address any as part of this planning round?"
- When the user says yes, the bug context is loaded and an issue is proposed for it
- When an issue that fixes a bug is completed, the bug's `fixed_by` field is updated and status set to `fixed`

## Acceptance criteria

- [ ] `/mantle:bug` is available in Claude Code and starts a brief structured bug capture
- [ ] Bug reports saved to `.mantle/bugs/<date>-<slug>.md` with YAML frontmatter
- [ ] Bug frontmatter includes date, author, summary, severity, status, related_issue, related_files, fixed_by, and tags
- [ ] The bug note is stamped with `git config user.email`
- [ ] Severity is suggested by the AI based on the description, confirmed by the user
- [ ] `mantle init` creates the `.mantle/bugs/` directory
- [ ] `/mantle:plan-issues` surfaces open bugs at the start of planning sessions
- [ ] When a bug-fixing issue is completed, the bug's status and fixed_by fields are updated
- [ ] `/mantle:help` updated to include `/mantle:bug`
- [ ] Tests verify bug note format, frontmatter schema, listing, and status updates

## Blocked by

- Blocked by issue-02 (needs `.mantle/` directory and vault.py)

## User stories addressed

_New user stories (not in original PRD — extends the workflow):_

- As a developer, I want to run `/mantle:bug` during a session to quickly capture a bug with structured metadata, so that bugs are logged immediately rather than forgotten or scattered across notes.
- As a developer, I want bugs saved as dated markdown files in `.mantle/bugs/` with severity and reproduction steps, so that they accumulate as a trackable backlog.
- As a developer, I want `/mantle:plan-issues` to surface open bugs when I start a planning session, so that I can decide whether to address them as part of the next batch of work.
- As a developer, I want bugs linked to the issue that fixes them, so that I can trace from bug discovery through to resolution.
