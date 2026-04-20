---
title: Jira orchestration command on top of lifecycle hook seam
status: planned
slice:
- cli
- claude-code
story_count: 0
verification: null
blocked_by: []
skills_required: []
tags:
- type/issue
- status/planned
acceptance_criteria:
- id: ac-01
  text: '`.mantle/config.md` schema documents Jira config keys.'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-02
  text: Lifecycle transitions push status updates to Jira via the hook seam (issue
    56's contract).
  passes: false
  waived: false
  waiver_reason: null
- id: ac-03
  text: Manual `mantle jira-link` command binds an existing Jira key to a Mantle issue.
  passes: false
  waived: false
  waiver_reason: null
- id: ac-04
  text: E2E test against a Jira sandbox (or mocked client) covers create + transition.
  passes: false
  waived: false
  waiver_reason: null
- id: ac-05
  text: README documents the Jira flow end-to-end.
  passes: false
  waived: false
  waiver_reason: null
- id: ac-06
  text: '`just check` passes.'
  passes: false
  waived: false
  waiver_reason: null
---

## Parent PRD

product-design.md, system-design.md

## Why

Issue 56 shipped the generic lifecycle hook seam plus a Jira example script. The original ask (inbox 2026-04-09: "Link mantle issues and stories to a team Jira kanban") is only ~50% delivered — the seam exists but there's no first-class `/mantle:jira` orchestration. Now that the seam is stable, the remaining work is small and well-scoped.

## What to build

A `/mantle:jira` Claude command and supporting CLI plumbing that:
- Reads Jira config from `.mantle/config.md` (board id, credentials reference, status mappings).
- Creates / updates Jira tickets when an issue is shaped, implementing, implemented, or verified — using the existing hook seam, not a parallel mechanism.
- Provides a `mantle jira-link --issue NN --jira-key ABC-123` command for manual binding when an issue pre-exists in Jira.

Shaping should decide: pure-hook approach (extend the example script to first-class), or a thin Python wrapper with stronger error reporting.

## Acceptance criteria

- [ ] ac-01: `.mantle/config.md` schema documents Jira config keys.
- [ ] ac-02: Lifecycle transitions push status updates to Jira via the hook seam (issue 56's contract).
- [ ] ac-03: Manual `mantle jira-link` command binds an existing Jira key to a Mantle issue.
- [ ] ac-04: E2E test against a Jira sandbox (or mocked client) covers create + transition.
- [ ] ac-05: README documents the Jira flow end-to-end.
- [ ] ac-06: `just check` passes.

## Blocked by

None (issue 56 shipped).

## User stories addressed

- As a Mantle user on a team using Jira, I want my mantle issues to appear and progress on the team board so colleagues can see what's in flight without me manually mirroring state.