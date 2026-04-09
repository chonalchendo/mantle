---
issue: 34
title: Auto-transition issue status in build pipeline
approaches:
- Prompt + minimal core wiring — add implemented status, CLI command, update prompts
  to call transitions
- Lifecycle observer — event-driven auto-transitions based on story/verification state
chosen_approach: Prompt + minimal core wiring
appetite: small batch
open_questions:
- Should transition_to_implementing be idempotent (no-op if already implementing)?
author: 110059232+chonalchendo@users.noreply.github.com
created: '2026-04-06'
updated: '2026-04-06'
updated_by: 110059232+chonalchendo@users.noreply.github.com
tags:
- type/shaped
- phase/shaping
---

## Chosen approach: Prompt + minimal core wiring

Wire existing transition commands into the build pipeline prompts, plus add the missing `implemented` status.

### Rationale

The building blocks already exist — `transition_to_implementing`, `transition_to_verified`, `transition_to_approved` are all implemented. The gap is:
1. No `implemented` status (between implementing and verified)
2. Prompts don't call these transitions

### Strategy

**core/issues.py** — Add `implemented` to `_ALLOWED_TRANSITIONS` as a target from `implementing`. Add `transition_to_implemented()` public function.

**cli/review.py** — Add `run_transition_to_implemented` CLI command wired to `transition-issue-implemented`.

**claude/commands/mantle/build.md** — Add transition calls:
- Step 6 start: `mantle transition-issue-implementing --issue {NN}`
- Step 6 end (all stories done): `mantle transition-issue-implemented --issue {NN}`
- Step 8 already handled by verify.md

**claude/commands/mantle/implement.md** — Add transition call at start to `mantle transition-issue-implementing --issue {NN}` (idempotent if already implementing).

### Fits architecture by

- `core/issues.py` owns issue lifecycle — adding a status follows the existing pattern
- CLI layer (`cli/review.py`) is the thin consumer — new command follows existing `transition-issue-*` pattern
- Prompts orchestrate, Python manages state — transitions happen via CLI calls from prompts
- No new modules, no new patterns

### Does not

- Does not add a lifecycle observer or event system (YAGNI)
- Does not auto-transition project state (state.md) — only issue status
- Does not change the verify.md or review.md prompts — they already handle their own transitions
- Does not add rollback logic — transitions are idempotent in the forward direction