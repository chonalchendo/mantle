---
title: Git branch and worktree integration for per-issue isolation
status: planned
slice:
- cli
- core
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
  text: '`/mantle:build NN` in `git_mode: branch` creates `issue-NN-<slug>` branch
    from current HEAD and commits to it; master untouched.'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-02
  text: '`/mantle:build NN` in `git_mode: worktree` creates a sibling worktree, runs
    the build there, leaves the user''s primary worktree untouched.'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-03
  text: '`git_mode: none` (default) preserves today''s behavior.'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-04
  text: PR-creation step (or instruction) is provided for `branch`/`worktree` modes.
  passes: false
  waived: false
  waiver_reason: null
- id: ac-05
  text: Tests cover branch creation, branch already-exists collision, and worktree
    path collision.
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

Mantle currently commits directly to `master` during `/mantle:build`. At work, direct commits to master are disallowed — branches per work item are required. Worktrees would also enable parallel work on multiple issues in the same repo without conflicts (inbox 2026-04-09). This is live work pain, not speculative.

## What to build

Two related capabilities (shaping should split if needed):
1. **Auto-branch per issue.** `/mantle:build` (or `/mantle:implement`) creates `issue-NN-<slug>` branch from base before any commit, and commits to it. Configurable: `disabled` | `branch` | `worktree`.
2. **Worktree mode.** When configured, create a sibling worktree at `../<repo>-issue-NN/` so the user can keep their main checkout on a different branch.

Config in `.mantle/config.md` frontmatter (e.g. `git_mode: branch | worktree | none`).

## Acceptance criteria

- [ ] ac-01: `/mantle:build NN` in `git_mode: branch` creates `issue-NN-<slug>` branch from current HEAD and commits to it; master untouched.
- [ ] ac-02: `/mantle:build NN` in `git_mode: worktree` creates a sibling worktree, runs the build there, leaves the user's primary worktree untouched.
- [ ] ac-03: `git_mode: none` (default) preserves today's behavior.
- [ ] ac-04: PR-creation step (or instruction) is provided for `branch`/`worktree` modes.
- [ ] ac-05: Tests cover branch creation, branch already-exists collision, and worktree path collision.
- [ ] ac-06: `just check` passes.

## Blocked by

None.

## User stories addressed

- As a Mantle user at work where master is protected, I want builds to commit to a per-issue branch so I can open PRs without breaking team policy.
- As a Mantle user juggling multiple in-progress issues, I want each build to run in its own worktree so I don't have to stash/checkout between contexts.