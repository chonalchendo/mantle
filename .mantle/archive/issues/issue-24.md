---
title: Simplify command (/mantle:simplify)
status: completed
slice:
- core
- cli
- claude-code
- tests
story_count: 2
verification: null
blocked_by: []
skills_required: []
tags:
- type/issue
- status/completed
acceptance_criteria:
- id: ac-01
  text: '`/mantle:simplify` is available in Claude Code and starts a simplification
    session'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-02
  text: 'Issue-scoped mode: accepts an issue number, collects changed files from issue''s
    story commits'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-03
  text: 'Standalone mode: operates on changed files from git status when no issue
    given'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-04
  text: Spawns per-file simplification agents with file contents, CLAUDE.md context,
    and LLM bloat pattern checklist
  passes: false
  waived: false
  waiver_reason: null
- id: ac-05
  text: 'LLM bloat checklist covers: unnecessary abstractions, defensive over-engineering,
    code duplication, unnecessary conditionals, dead code, comment noise, slop scaffolding,
    over-parameterisation'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-06
  text: Tests run before and after simplification to verify behavioral equivalence
  passes: false
  waived: false
  waiver_reason: null
- id: ac-07
  text: Changes committed separately from implementation commits
  passes: false
  waived: false
  waiver_reason: null
- id: ac-08
  text: Language-agnostic — no hardcoded language-specific rules
  passes: false
  waived: false
  waiver_reason: null
---

## Parent PRD

product-design.md, system-design.md

## What to build

The `/mantle:simplify` command — a post-implementation quality gate that identifies and removes characteristic AI-generated code bloat. Language-agnostic, driven by the project's CLAUDE.md standards and a universal LLM bloat pattern checklist.

Two modes of operation:

- **Issue-scoped** (default): `/mantle:simplify 15` collects the git diff for an issue's story commits, identifies changed files, and spawns per-file simplification agents. Each agent receives the file contents, CLAUDE.md standards, and the bloat pattern checklist. Tests run after all files are processed. Surviving changes committed as `refactor(issue-N): simplify implementation`.
- **Standalone**: `/mantle:simplify` with no arguments operates on changed files from git status. Can also accept explicit file paths. Works outside the Mantle issue workflow.

This includes:

- `claude/commands/mantle/simplify.md` — Claude Code command that orchestrates the simplification pass, spawning per-file agents
- No core module or CLI commands needed — this is a prompt-only orchestrator (like implement.md) that uses git and existing mantle CLI commands

## Acceptance criteria

- [ ] ac-01: `/mantle:simplify` is available in Claude Code and starts a simplification session
- [ ] ac-02: Issue-scoped mode: accepts an issue number, collects changed files from issue's story commits
- [ ] ac-03: Standalone mode: operates on changed files from git status when no issue given
- [ ] ac-04: Spawns per-file simplification agents with file contents, CLAUDE.md context, and LLM bloat pattern checklist
- [ ] ac-05: LLM bloat checklist covers: unnecessary abstractions, defensive over-engineering, code duplication, unnecessary conditionals, dead code, comment noise, slop scaffolding, over-parameterisation
- [ ] ac-06: Tests run before and after simplification to verify behavioral equivalence
- [ ] ac-07: Changes committed separately from implementation commits
- [ ] ac-08: Language-agnostic — no hardcoded language-specific rules

## Blocked by

_None_

## User stories addressed

- No existing user story — new capability identified during project development