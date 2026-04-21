---
title: Model-tier config with measured defaults for the build pipeline
status: approved
slice:
- core
- cli
- claude-code
story_count: 5
verification: null
blocked_by: []
skills_required:
- CLI design best practices
- Design Review
- Designing Architecture
- DuckDB Best Practices and Optimisations
- DuckLake
- Earnings Transcript Data Sources
- EarningsCall.biz Scraping
- FRED Data Source
- Howard Marks Investment Philosophy
- John Templeton Investment Philosophy
- Lakehouse Architecture
- Macrotrends Data Source
- Medallion Architecture & Star Schema
- Mohnish Pabrai Investment Philosophy
- Nick Sleep Investment Philosophy
- OpenRouter LLM Gateway
- Playwright Web Scraping
- Production Project Readiness
- Python 3.14
- Python Project Conventions
- Python package structure
- SQLMesh Best Practices
- Software Design Principles
- Tom Gayner Investment Philosophy
- beautifulsoup4-web-scraping
- claude-sdk-structured-analysis-pipelines
- cyclopts
- dirty-equals
- docker-compose-python
- edgartools
- fastapi
- httpx-async
- import-linter
- inline-snapshot
- omegaconf
- pydantic-discriminated-unions
- pydantic-project-conventions
- python-314
- streamlit
- streamlit-aggrid
tags:
- type/issue
- status/approved
---

## Parent PRD

product-design.md, system-design.md

## Why

`/mantle:build` on a work API budget is dominated by Opus-4.7 cost on stages that don't need Opus-grade reasoning (file edits, test runs, commits, mechanical verification). Swapping those stages to Sonnet or Haiku is a ~5× cost reduction and a material speed-up — a step change no amount of prompt pruning can match. The other cost-optimisation threads (prompt pruning, review+retrospective merge, `.mantle/` restructure) were bundled into this issue originally; they're real but each deserves its own narrowly-scoped issue. See `.mantle/learnings/` for the scope-creep learning that drove the split.

This issue ships the dominant lever — per-stage model tiering with a cost-policy doc — and a measured baseline so follow-up work has evidence to calibrate against.

## What to build

1. **Policy doc (`.mantle/cost-policy.md`)** naming three presets (`budget`, `balanced`, `quality`) with per-stage model defaults and a one-line rationale for each stage's choice. Stages: `shape`, `plan_stories`, `implement`, `simplify`, `verify`, `review`, `retrospective`.
2. **Config schema** (`.mantle/config.md` frontmatter) with a `models:` block that selects an active preset and allows per-stage overrides. Validated by a Pydantic model in `core/config.py`.
3. **`build.md` wiring** so each spawned Agent receives the correct per-stage model, pulled from the active preset with per-stage overrides applied.
4. **`.mantle/telemetry/` folder** introduced, used to hold the before/after measurement for ac-04 (and future telemetry outputs from follow-up issues).
5. **Measured before/after** for one `/mantle:build` run on the same issue, under the previous all-Opus default and under the new `balanced` preset. Measure dollar cost and wall-clock seconds — not token counts.

## Acceptance criteria

- [ ] ac-01: `.mantle/cost-policy.md` exists and documents three named presets (`budget`, `balanced`, `quality`) with per-stage model defaults and a short rationale.
- [ ] ac-02: `.mantle/config.md` schema includes a validated `models:` block that selects an active preset (with optional per-stage overrides); `core/config.py` round-trips it.
- [ ] ac-03: `build.md` reads the active tier from `config.md` / `cost-policy.md` and passes the per-stage model to each spawned agent (shape, plan-stories, implement, simplify, verify).
- [ ] ac-04: A before/after measurement of one `/mantle:build` run on the same issue is saved to `.mantle/telemetry/baseline-<date>.md`, reporting wall-clock seconds and dollar cost (not just token counts). The telemetry folder is introduced by this issue.
- [ ] ac-05: `just check` passes.

## Blocked by

None. Supersedes issue 75's scope; 75 should be archived or kept only for the A/B harness piece (which is deferred — one manual before/after comparison is enough for this issue).

## User stories addressed

- As a Mantle user on API billing, I want the build pipeline to spend Opus tokens only where Opus-grade reasoning earns them, so I don't pay 5× for mechanical steps.
- As a maintainer, I want one authoritative policy doc naming default models per stage, so cost choices are visible and revisable in one place rather than scattered across prompts.
- As a Mantle user considering a cheaper tier, I want a measured before/after dollar + time comparison, so the trade-off against Opus is evidence-backed not taste-driven.

## Deferred to follow-up issues

These were part of the original umbrella and should each become their own narrow issue:

- **AI-led review + retrospective** (or merging them into one command). 1–2 days.
- **Prune build-pipeline prompts** (`build.md`, `shape-issue.md`, `plan-stories.md`, `implement.md`, `simplify.md`, `verify.md`). Likely a one-session editing pass after model tiering ships — revisit size once Opus tax is fixed.
- **A/B harness** (automated side-by-side strategy comparison). Only if one manual comparison isn't enough.
- **`.mantle/` restructure** (move `sessions/`, `builds/`, `learnings/` under `telemetry/`). Breaking change; schedule for a planned breaking release.

## Source inbox items

- `2026-04-20-optimise-mantle-for-costcontex.md`
- `2026-04-09-ab-test-modeleffort-strategy.md` (informs the deferred A/B harness issue)
- `2026-04-16-model-tiering-strategy.md`
