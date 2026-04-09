---
title: Fix hardcoded .mantle/ path reads in Claude Code prompts
status: planned
slice:
- claude-code
- cli
story_count: 0
verification: null
blocked_by: []
skills_required: []
tags:
- type/issue
- status/planned
---

## Parent PRD

product-design.md, system-design.md

## Why

Issue 43 (archived) added global `.mantle/` storage mode — projects can opt to store state under `~/.mantle/projects/<identity>/` instead of a local `.mantle/` directory. The CLI layer was migrated to route all path access through `core/project.resolve_mantle_dir()`, but the 20 Claude Code prompt files under `claude/commands/mantle/*.md` were never swept. They still read paths like `.mantle/state.md`, `.mantle/product-design.md`, and `.mantle/issues/` directly with the Read tool.

The result: when a project is in global storage mode, prompts like `/mantle:adopt` (line 45: "Check whether `.mantle/` and `.mantle/state.md` exist by reading them") stumble — they look in the local project directory first, find nothing, and either fail or mislead. This silently breaks the entire global-mode workflow for Claude Code users, which was the whole point of issue 43.

Issue 43's own learning note explicitly flagged that Story 2 (22+ source modules) was already at the edge of what a single agent could handle, and the prompt sweep was deferred out of scope. This issue closes that gap.

## What to build

1. **A CLI command that prints the resolved `.mantle/` absolute path** — a thin wrapper around the existing `project.resolve_mantle_dir()` function. Prompts can shell out to it and read the returned path instead of hardcoding `.mantle/`. Candidate names: `mantle where`, `mantle resolve-path`, or extending the existing `introspect-project` command.

2. **A full sweep of `claude/commands/mantle/*.md`** — 20 prompt files currently hardcode `.mantle/` path reads. Each must be updated to call the new CLI command first, then read from the returned path. The 20 affected files (from grep): `adopt.md`, `add-issue.md`, `add-skill.md`, `brainstorm.md`, `bug.md`, `build.md`, `design-product.md`, `design-system.md`, `fix.md`, `implement.md`, `plan-issues.md`, `plan-stories.md`, `retrospective.md`, `review.md`, `revise-product.md`, `revise-system.md`, `scout.md`, `shape-issue.md`, `simplify.md`, `verify.md`.

3. **Tests** — a unit test for the new resolver command and an integration test that confirms a global-mode project's prompt workflow resolves correctly.

### Flow

1. User runs `mantle init --global` (future work in a follow-up issue) or manually migrates via `mantle storage --mode global` today. No local `.mantle/` exists in the project directory.
2. User runs `/mantle:adopt` (or any other prompt) in Claude Code.
3. Prompt's first step calls the new CLI command to resolve the `.mantle/` path.
4. Prompt reads `state.md`, `product-design.md`, etc. from the resolved absolute path — which points at `~/.mantle/projects/<identity>/` in global mode, or the local `.mantle/` in local mode.
5. Workflow succeeds identically in both storage modes.

## Acceptance criteria

- [ ] A CLI command exists that prints the resolved `.mantle/` absolute path via `project.resolve_mantle_dir()`, usable from any prompt with a single shell call
- [ ] All 20 `claude/commands/mantle/*.md` prompts that currently read `.mantle/` paths directly are updated to resolve via the new command first
- [ ] `/mantle:adopt` works end-to-end in a project with `storage_mode: global` (no local `.mantle/` present)
- [ ] A grep audit of `claude/commands/mantle/*.md` confirms no remaining hardcoded `.mantle/` path reads (excluding intentional mentions in help text, examples, or comments)
- [ ] Unit test covering the new CLI command
- [ ] Integration test simulating a global-mode prompt workflow (prompt resolves path, reads state, returns successfully)

## Blocked by

None. Issue 43 landed the `resolve_mantle_dir()` resolver and the storage-mode migration commands; this builds on top of that foundation.

## User stories addressed

- As a developer using Mantle in a work repo where I cannot check in `.mantle/`, I want `/mantle:adopt` and other Claude Code commands to work in global storage mode so that I can use Mantle's full workflow without polluting the work repo.
- As a developer switching between local and global storage modes, I want prompts to transparently find the right `.mantle/` directory so that storage mode is an implementation detail, not a workflow difference.