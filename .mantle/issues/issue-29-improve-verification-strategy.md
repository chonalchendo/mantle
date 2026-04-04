---
title: Improve verification strategy — structured first-use and prompted evolution
status: planned
slice:
- claude-code
- core
story_count: 3
verification: null
blocked_by: []
tags:
- type/issue
- status/planned
---

## Parent PRD

product-design.md, system-design.md

## Why

The current verification strategy is a single free-text string saved on first use. Users write something vague ("run pytest and check"), it gets stored verbatim, and every subsequent verification run either ignores the strategy or the user has to manually override it. When users correct the AI during verification ("no, run this command and check S3 output"), that feedback is lost — the strategy never updates, so the same correction happens every time.

Two problems:
1. **First-use is too shallow** — no project introspection, no structure, no guidance. Users get a blank "describe your strategy" prompt and write whatever comes to mind.
2. **Strategy doesn't evolve** — corrections during verification are lost. The user repeats themselves every build cycle.

## What to build

### 1. Structured first-use with project introspection

When no verification strategy exists, the verify prompt should:

1. **Introspect the project** — read CLAUDE.md for test/check commands, detect test framework from config files (pyproject.toml, package.json, Cargo.toml), check for CI config, check for Justfile/Makefile
2. **Propose a structured strategy** with sections:
   - Test command (detected from project)
   - Lint/type check command (if found)
   - Acceptance criteria verification approach (how to check each criterion)
   - Smoke test / integration check (optional — project-specific commands)
3. **Ask user to confirm or adjust** before saving

### 2. Prompted strategy evolution

After verification completes (Step 7 in verify.md), if the user corrected any verification approach during the session (e.g. "run just ingest instead", "check the S3 output"), the verify prompt should:

1. Detect that the user provided verification guidance not captured in the current strategy
2. Ask: "Should I update the verification strategy to include {change}?"
3. If confirmed, update via `mantle save-verification-strategy`

This is prompted, not silent — the user always confirms before the strategy changes.

### 3. Build pipeline alignment

The build pipeline's verify override ("if no strategy, use a sensible default") should use the same project introspection logic — auto-generate a structured strategy non-interactively and save it, so future runs have a real strategy.

## Acceptance criteria

- [ ] First-use flow introspects project files (CLAUDE.md, pyproject.toml, Justfile, etc.) before proposing a strategy
- [ ] Proposed strategy is structured with sections (test command, lint, AC verification, smoke test)
- [ ] User confirms or adjusts the proposed strategy before it's saved
- [ ] After verification, if user corrected the approach, prompt asks whether to update the strategy
- [ ] Strategy updates are persisted via `mantle save-verification-strategy`
- [ ] Build pipeline auto-generates a structured strategy when none exists (non-interactive)
- [ ] Existing strategies are preserved — changes only append or refine, never silently overwrite

## Blocked by

None

## User stories addressed

- As a developer, I want my verification strategy to be auto-detected from my project setup so I don't have to describe it from scratch
- As a developer, I want corrections I give during verification to persist so I don't repeat myself every build cycle