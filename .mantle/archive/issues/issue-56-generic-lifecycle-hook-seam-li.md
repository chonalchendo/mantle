---
title: Generic lifecycle hook seam (Linear/Jira as first examples)
status: approved
slice:
- core
- cli
- claude-code
story_count: 3
verification: null
blocked_by: []
skills_required:
- CLI design best practices
- Design Review
- FRED Data Source
- John Templeton Investment Philosophy
- Python 3.14
- Python package structure
- SQLMesh Best Practices
- Software Design Principles
- cyclopts
- edgartools
- fastapi
- httpx-async
- omegaconf
- pydantic-discriminated-unions
- pydantic-project-conventions
- python-314
- streamlit
- streamlit-aggrid
tags:
- type/issue
- status/approved
acceptance_criteria:
- id: ac-01
  text: Mantle invokes `<mantle-dir>/hooks/on-<event>.sh` on each emitted lifecycle
    event with documented positional args (issue id, new status, issue title)
  passes: false
  waived: false
  waiver_reason: null
- id: ac-02
  text: 'Lifecycle events emitted cover: issue-shaped, issue-implement-start, issue-verify-done,
    issue-review-approved'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-03
  text: '`hooks.env:` keys from `config.yml` are exported as environment variables
    to the hook process'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-04
  text: Hooks directory resolution works for both global `~/.mantle/` and per-project
    `.mantle/` via `mantle where`
  passes: false
  waived: false
  waiver_reason: null
- id: ac-05
  text: Missing hook script is a no-op (no error, no warning noise)
  passes: false
  waived: false
  waiver_reason: null
- id: ac-06
  text: Hook script failures log a warning but do not block mantle's workflow
  passes: false
  waived: false
  waiver_reason: null
- id: ac-07
  text: 'Shipped example: `linear.sh` works end-to-end against a real Linear workspace
    (GraphQL via curl)'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-08
  text: 'Shipped example: `jira.sh` works end-to-end against a real Jira instance
    (via `acli`)'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-09
  text: 'Shipped example: `slack.sh` posts a message to a Slack incoming webhook'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-10
  text: Each example script has a setup header documenting install + auth + required
    env vars
  passes: false
  waived: false
  waiver_reason: null
- id: ac-11
  text: README section documents the hook authoring convention
  passes: false
  waived: false
  waiver_reason: null
- id: ac-12
  text: Covered by tests (event emission, arg passing, env passthrough, missing-hook
    no-op, failure-does-not-block)
  passes: false
  waived: false
  waiver_reason: null
---

## Parent PRD

product-design.md, system-design.md

## Why

There's no way today for mantle to notify external tools when issue lifecycle events happen. Users who track work in a team board (Jira, Linear, etc.) end up double-entering — writing a mantle issue, then mirroring status into the team tracker — and teammates have no visibility into what's in progress between standups.

Rather than ship a Jira-specific (or Linear-specific) integration — which would drag mantle toward being a PM tool and violate the "no PM features / Obsidian-native" constraints in product-design.md — expose a generic extension seam. Mantle emits lifecycle events; user-supplied shell scripts handle the push to whichever tracker they use. Mantle never imports a tracker library, never holds credentials, never knows which tool is on the other end.

This matches the pattern already named as a future-extensibility path in product-design.md (`/mantle:sync-notion` one-way export) and the pattern used by pre-commit, git hooks, and GitHub Actions.

## What to build

A hook-dispatch mechanism in mantle's core, a config passthrough for tracker-specific settings, and a set of shipped example scripts covering the common cases (Linear, Jira, Slack).

### Flow

1. User runs a command that triggers a lifecycle event (e.g., `/mantle:shape-issue`, `/mantle:verify`, `/mantle:review` approval).
2. Mantle resolves the hooks directory via `mantle where` → `<mantle-dir>/hooks/`.
3. If a script matching the event name exists (e.g., `on-issue-shaped.sh`), mantle invokes it with positional args: issue id, new status, issue title.
4. Before invoking, mantle reads `hooks.env:` from `config.yml` and exports each key/value as an environment variable for the hook process. Keys are opaque — mantle never interprets them.
5. Hook runs the user's chosen CLI/API call (e.g., `acli jira work-item update`, a Linear GraphQL curl, a Slack webhook).
6. On hook failure, mantle logs a warning and continues — hook errors do not block the workflow.
7. Missing hook scripts are a no-op.

## Acceptance criteria

- [ ] ac-01: Mantle invokes `<mantle-dir>/hooks/on-<event>.sh` on each emitted lifecycle event with documented positional args (issue id, new status, issue title)
- [ ] ac-02: Lifecycle events emitted cover: issue-shaped, issue-implement-start, issue-verify-done, issue-review-approved
- [ ] ac-03: `hooks.env:` keys from `config.yml` are exported as environment variables to the hook process
- [ ] ac-04: Hooks directory resolution works for both global `~/.mantle/` and per-project `.mantle/` via `mantle where`
- [ ] ac-05: Missing hook script is a no-op (no error, no warning noise)
- [ ] ac-06: Hook script failures log a warning but do not block mantle's workflow
- [ ] ac-07: Shipped example: `linear.sh` works end-to-end against a real Linear workspace (GraphQL via curl)
- [ ] ac-08: Shipped example: `jira.sh` works end-to-end against a real Jira instance (via `acli`)
- [ ] ac-09: Shipped example: `slack.sh` posts a message to a Slack incoming webhook
- [ ] ac-10: Each example script has a setup header documenting install + auth + required env vars
- [ ] ac-11: README section documents the hook authoring convention
- [ ] ac-12: Covered by tests (event emission, arg passing, env passthrough, missing-hook no-op, failure-does-not-block)

## Brainstorm reference

.mantle/brainstorms/2026-04-12-jira-integration-via-hook-seam.md

## Blocked by

None

## User stories addressed

- As a developer using mantle at work, I want lifecycle events to push status updates to my team's Linear/Jira board, so that teammates can see what I'm working on without me double-entering.
- As a developer, I want the integration mechanism to be tool-agnostic, so that switching trackers (or adding Slack notifications) doesn't require a mantle update.
- As a developer, I want mantle to never touch my tracker credentials, so that auth stays in my local CLI tools' keychain/env where it belongs.

## Open questions (for shape-issue)

- Sync vs async hook execution: blocking surfaces failures immediately but can slow the workflow; fire-and-forget is faster but hides broken hooks.
- Exact event naming scheme and full list — above is a starter set; shape step should confirm completeness.