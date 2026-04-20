---
title: 'Cost and context optimisation: model routing, streamlined prompts, AI-led
  review/retrospective'
status: planned
slice:
- claude-code
- cli
- core
story_count: 0
verification: null
blocked_by: []
skills_required: []
tags:
- type/issue
- status/planned
acceptance_criteria: []
---

## Parent PRD

product-design.md, system-design.md

## Why

Work has moved to API per-usage billing, so every token has real cost and Sonnet 4.6's 200k window is the constraint. Heavy commands like /mantle:build must fit that budget. On the personal side, Opus 5-hour rate limits get hit fast across multiple projects, so efficiency also reduces waiting.

Three threads collapse into one umbrella because they share the same driver (cost per invocation) and intersect heavily (streamlining review/retrospective IS context optimisation):

1. **Model routing** — Opus only where deep reasoning earns it (shape, plan, decision gates); Sonnet for implementation and most prompt work; Haiku for deterministic steps. Composes with existing issue 75 (model tiering config) — that issue delivers the knobs; this one delivers the defaults and rationale.
2. **Context budgeting** — audit compiled payloads, skills graph, and prompt prose so a full /mantle:build run fits inside 200k. Composes with existing issues 74 (token audit of /mantle:* commands) and 79 (progressive-disclosure audit of CLAUDE.md + .mantle/) — those measure; this one acts on the findings.
3. **AI-led review and retrospective** — today /mantle:review and /mantle:retrospective force Q&A that the user often has nothing to add to. Make them AI-led reflection with optional human interjection, saving a full turn each.

## What to build

Treat this as a programme, not a single patch. Expected shape:

- A short cost/context policy document in `.mantle/` that names defaults (which model at which stage, target token budgets for /mantle:build, etc.).
- Concrete edits to at least /mantle:review and /mantle:retrospective that convert the mandatory Q&A into an AI-led summary with an optional "anything to add?" hook.
- Apply the streamlining lens to the top N highest-frequency command prompts (driven by the 74 / 79 findings).
- Defaults wired into model tiering (issue 75) so a greenfield install gets a sensible cost/quality starting point.

## Acceptance criteria

- [ ] ac-01: A short cost/context policy document lives in `.mantle/` naming default model per workflow stage and a target token budget for /mantle:build.
- [ ] ac-02: /mantle:review and /mantle:retrospective run AI-led by default; human interjection is optional, not forced.
- [ ] ac-03: A measured before/after token comparison for one high-frequency command is recorded (e.g. in a learning) showing a meaningful reduction without quality regression.
- [ ] ac-04: Model-tier defaults (in the config surface delivered by issue 75) reflect the policy document.
- [ ] ac-05: `just check` passes.

## Blocked by

- issue 75 (model tiering config) — ideally ships first so defaults have somewhere to live. Not strictly required for the /mantle:review and /mantle:retrospective streamlining.
- Composes with issue 74 (token audit of /mantle:* commands) and issue 79 (context file audit) — use their outputs to choose where to cut.

## User stories addressed

- As a mantle user on API billing, I want /mantle:build to finish inside the Sonnet 200k window so heavy runs don't overflow context.
- As a mantle user running review and retrospective, I want AI-led reflection by default so I don't waste a turn answering questions I have no input on.
- As a maintainer, I want one canonical policy document so cost choices are visible and revisable rather than scattered across commands.

## Source inbox items

- `2026-04-20-optimise-mantle-for-costcontex.md`
- `2026-04-20-streamline-mantlereview-and-ma.md`