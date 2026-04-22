---
title: Extend mantle audit-tokens to sweep all commands and skills in the vault
status: implementing
slice:
- core
- cli
- claude-code
- tests
story_count: 2
verification: null
blocked_by: []
skills_required:
- CLI design best practices
- Design Review
- OpenRouter LLM Gateway
- Software Design Principles
- claude-sdk-structured-analysis-pipelines
- python-314
tags:
- type/issue
- status/implementing
acceptance_criteria: []
---

## Parent PRD

product-design.md, system-design.md

## Why

Issue 74 audited only `claude/commands/mantle/*.md` (29 files) and cut the top-3 by ~20% each for a 4.6% total reduction. Every *other* command in `claude/commands/` and every skill node in the skill vault is also prose that ships into Claude sessions on every invocation — and skills are the larger surface by far.

Follow-up from the issue 74 retrospective (2026-04-22): 'Extend audit to ALL commands + skills in the vault' and 'Every /mantle:* command that emits output should have an Output Format section — durable output discipline, not just a trim technique.'

Distinct from issue 79 (which audits CLAUDE.md + `.mantle/` artifact files, a different surface). The measurement instrument (`mantle audit-tokens`) is shared; the paths and ranking are what change.

## What to build

- `mantle audit-tokens` accepts multiple paths (or a config-driven sweep list) so one invocation covers commands + skills in a single combined report.
- Audit report covers all `claude/commands/**/*.md` and every skill node in the vault, ranked by token cost. Separate sub-tables per surface for readability.
- Top-3 commands and top-3 skills (by token cost) get concrete cuts using the Output Format template + imperative-fragment rewrite techniques proven on issue 74.
- Every `/mantle:*` command that emits any output gets an Output Format section with a one-line-per-item template and a short anti-pattern list. Not optional, not limited to top-3.
- Before/After/Delta report generated via `--append`. Report lives under `.mantle/audits/`.

## Scope boundaries

- Preserve Iron Laws, Red Flags tables, numbered-step structure, CLI invocations, and `$MANTLE_DIR`/`.mantle/` paths in every rewrite.
- Do not touch CLAUDE.md or `.mantle/` artifact files — those belong to issue 79.
- Output-token savings (real `claude -p` runs) stay deferred (issue 74's approach C).

## Acceptance criteria

- [ ] ac-01: Audit report lists every command (`claude/commands/**/*.md`) and every skill in the vault with token counts, ranked by cost, with separate sub-tables per surface.
- [ ] ac-02: Top-3 commands AND top-3 skills (by token cost) get concrete cuts applied.
- [ ] ac-03: Every `/mantle:*` command that emits any output has an Output Format section (with one-line template + anti-pattern list).
- [ ] ac-04: Total token savings measured and reported via `mantle audit-tokens --append` in the same report.
- [ ] ac-05: No behavioral regression — existing `/mantle:build` runs end-to-end on a test issue.
- [ ] ac-06: `just check` passes.

## Blocked by

None (builds on issue 74).

## User stories addressed

- As a Mantle user paying for tokens on every AI invocation, I want the full command + skill surface audited and pruned so recurring cost shrinks without losing capability.
- As a maintainer, I want AI outputs to follow a consistent terse pattern across every `/mantle:*` command, not just the top-3 most expensive ones.
- As a future me running audits quarterly, I want one command that sweeps the full vault surface so the audit cost is near zero.