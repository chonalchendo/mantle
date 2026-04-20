---
title: Issue planning (/mantle:plan-issues)
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
- status/planned
acceptance_criteria:
- id: ac-01
  text: '`/mantle:plan-issues` is available in Claude Code and starts an interactive
    issue planning session'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-02
  text: Issues are proposed one at a time — user approves or adjusts each before the
    next
  passes: false
  waived: false
  waiver_reason: null
- id: ac-03
  text: Each issue is a vertical slice cutting through multiple integration layers
  passes: false
  waived: false
  waiver_reason: null
- id: ac-04
  text: Each issue includes testable acceptance criteria defining "done"
  passes: false
  waived: false
  waiver_reason: null
- id: ac-05
  text: Issues are saved to `.mantle/issues/issue-<nn>.md` with YAML frontmatter
  passes: false
  waived: false
  waiver_reason: null
- id: ac-06
  text: Issue frontmatter includes title, status (planned), slice, blocked-by, and
    tags
  passes: false
  waived: false
  waiver_reason: null
- id: ac-07
  text: After each issue is approved, the command analyzes design impact and prompts
    the user to run `/mantle:revise-product` or `/mantle:revise-system` if relevant
  passes: false
  waived: false
  waiver_reason: null
- id: ac-08
  text: Impact prompts identify the specific section(s) of the design doc likely affected
  passes: false
  waived: false
  waiver_reason: null
- id: ac-09
  text: Project state transitions to "planning"
  passes: false
  waived: false
  waiver_reason: null
- id: ac-10
  text: Tests verify issue file format, frontmatter structure, and sequential numbering
  passes: false
  waived: false
  waiver_reason: null
---

## Parent PRD

product-design.md, system-design.md

## What to build

The `/mantle:plan-issues` Claude Code command that breaks work into vertical slice issues. The AI proposes one issue at a time — the user approves or adjusts each before the next is proposed. Each issue is a thin vertical slice with testable acceptance criteria, saved to `.mantle/issues/`.

This includes:
- `claude/commands/mantle/plan-issues.md` — static command prompt guiding one-at-a-time issue planning with vertical slice rules
- `vault-templates/issue.md` — Obsidian note template for issues
- Integration with `core/vault.py` for issue file creation
- Integration with `core/state.py` for state transition to "planning"
- Issue schema: title, status, slice (layers touched), acceptance criteria, blocked-by references, user stories

### Design impact analysis

After each issue is approved, the command analyzes whether the issue implies changes to `product-design.md` or `system-design.md` (e.g., new API surface, changed scope, architectural impact). If so, it prompts the user:

> "This issue touches the API layer. Consider running `/mantle:revise-system` to update the API contracts section."

The command does not edit design docs itself — it identifies the impact and defers to the revise commands, respecting one-command-one-job. The decision log entry created by `/mantle:revise-*` links back to the triggering issue via the `scope` field.

## Acceptance criteria

- [ ] ac-01: `/mantle:plan-issues` is available in Claude Code and starts an interactive issue planning session
- [ ] ac-02: Issues are proposed one at a time — user approves or adjusts each before the next
- [ ] ac-03: Each issue is a vertical slice cutting through multiple integration layers
- [ ] ac-04: Each issue includes testable acceptance criteria defining "done"
- [ ] ac-05: Issues are saved to `.mantle/issues/issue-<nn>.md` with YAML frontmatter
- [ ] ac-06: Issue frontmatter includes title, status (planned), slice, blocked-by, and tags
- [ ] ac-07: After each issue is approved, the command analyzes design impact and prompts the user to run `/mantle:revise-product` or `/mantle:revise-system` if relevant
- [ ] ac-08: Impact prompts identify the specific section(s) of the design doc likely affected
- [ ] ac-09: Project state transitions to "planning"
- [ ] ac-10: Tests verify issue file format, frontmatter structure, and sequential numbering

## Blocked by

- Blocked by issue-02 (needs `.mantle/` directory and vault.py)

## User stories addressed

- User story 18: Issues proposed one at a time with user approval
- User story 19: Each issue includes testable acceptance criteria
