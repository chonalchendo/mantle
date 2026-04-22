---
title: Audit /mantle:* commands for token-cost conciseness
status: implementing
slice:
- claude-code
story_count: 2
verification: null
blocked_by: []
skills_required:
- Design Review
- Designing Architecture
- Software Design Principles
- import-linter
- pydantic-discriminated-unions
- python-314
tags:
- type/issue
- status/implementing
acceptance_criteria:
- id: ac-01
  text: Audit report lists every command's token count and ranks by cost.
  passes: false
  waived: false
  waiver_reason: null
- id: ac-02
  text: Concrete cuts applied to at least the top 3 commands.
  passes: false
  waived: false
  waiver_reason: null
- id: ac-03
  text: Total token savings measured and reported.
  passes: false
  waived: false
  waiver_reason: null
- id: ac-04
  text: No behavioral regression — existing `/mantle:build` runs end-to-end.
  passes: false
  waived: false
  waiver_reason: null
- id: ac-05
  text: '`just check` passes.'
  passes: false
  waived: false
  waiver_reason: null
---

## Parent PRD

product-design.md, system-design.md

## Why

`/mantle:*` commands accumulated prose over many iterations. Some steps may be redundant or overly verbose, costing tokens on every invocation (inbox 2026-04-15). This is investigation-shaped: measure first, decide what to cut.

## What to build

An investigation pass with concrete deliverables:
- Token-count each `claude/commands/mantle/*.md` file.
- Identify the top 3-5 commands by token cost.
- For each, propose specific cuts using two primary techniques (see "Scout inputs" below) alongside the usual redundant-prose / duplicate-step / pruneable-example sweep.
- Land cuts that preserve behavior; defer or split out anything ambiguous.

## Scout inputs

The caveman scout (`.mantle/scouts/2026-04-21-caveman.md`, findings 7 and 8) surfaced two concrete techniques that should anchor the audit, rather than the open-ended "make it shorter":

1. **Explicit Output Format templates** — for any command whose output is machine-consumed or user-scanned (`/mantle:verify`, `/mantle:review`, `/mantle:status`, etc.), add an Output Format section with a one-line-per-item template and a short anti-pattern list ("no 'I noticed'", "no restating"). This cuts output drift and lets the prompt itself be shorter because the model is anchored to a template rather than prose style guidance.

2. **Rewrite prompts in the style they prescribe** — caveman's own SKILL.md and command files are written in the terse imperative-fragment style they ask the model to produce. Mantle commands currently model verbosity by example. During the audit pass, rewrite iron-law sections and numbered steps in imperative fragments, preserving Mantle's explicit-step structure but tightening prose inside each step. Target 20-30% per-command reduction.

These two techniques are the highest-ROI ways to land ac-02 ("concrete cuts applied"); generic prose-trimming is second-order.

## Measurement method

- **ac-01, ac-03 (prompt-file token counts)**: use
  `tiktoken.get_encoding("cl100k_base")` via the `mantle audit-tokens`
  subcommand. **Originally pinned to `anthropic.messages.count_tokens`;
  switched during implementation** after discovering Anthropic requires a
  funded account to access even nominally-free endpoints (Claude Code's
  OAuth does not grant API access). Tiktoken cl100k_base is the
  community-standard Claude proxy — ~97% accurate against real Claude
  BPE on English prose, with rank order and delta percentages
  effectively exact. Since the audit is rank-and-delta-based (not
  absolute-count-based), this accuracy tradeoff is acceptable.
- **Validating ac-02's rewrites make *outputs* terser, not just
  prompts** (optional, deferred): caveman's two-stage architecture applies —
  `evals/llm_run.py` generates outputs locally via real `claude -p`
  under baseline / terse-control / terse+rewritten arms and commits a
  snapshot JSON; `evals/measure.py` tokenizes the snapshot in CI. For
  this issue we measure prompt-file savings only. Output-token savings
  are a follow-up if the cost case warrants it — output tokens dominate
  on long agentic runs, but measuring them requires paid `claude -p`
  inference.

## Acceptance criteria

- [ ] ac-01: Audit report lists every command's token count and ranks by cost.
- [ ] ac-02: Concrete cuts applied to at least the top 3 commands.
- [ ] ac-03: Total token savings measured and reported.
- [ ] ac-04: No behavioral regression — existing `/mantle:build` runs end-to-end.
- [ ] ac-05: `just check` passes.

## Blocked by

None.

## User stories addressed

- As a Mantle user paying for tokens on every `/mantle:*` invocation, I want command prose pruned of redundancy so my recurring cost shrinks without losing the workflow guarantees.