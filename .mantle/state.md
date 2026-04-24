---
schema_version: 1
project: mantle
status: planning
confidence: 0/10
created: '2026-02-22'
created_by: conal@conalnicholson.com
updated: '2026-04-24'
updated_by: 110059232+chonalchendo@users.noreply.github.com
current_issue: null
current_story: null
slices:
- core
- cli
- claude-code
- tests
skills_required:
- CLI design best practices
- Design Review
- Designing Architecture
- DuckDB Best Practices and Optimisations
- DuckLake
- Earnings Transcript Data Sources
- EarningsCall.biz Scraping
- FRED Data Source
- Finnhub Data Source
- Finviz Data Source
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
- python
- python-314
- streamlit
- streamlit-aggrid
tags:
- status/active
---

## Summary

AI workflow engine with persistent context, integrated with Claude Code and Obsidian.

## Current Focus

Learning captured for issue 91 — review past learnings before next planning cycle.

## Blockers

_None_

## Next Steps

Issues are grouped under target releases. Order within a bucket is the implementation order; releases ship when all issues in the bucket reach `verified`.

### v0.22.0 — Telemetry fix (ready to ship)

- Issue 91 — fix SessionStart hook to write `.mantle/.session-id` ✓ verified

### v0.23.0 — Regression-safety net

- Issue 90 — prompt-layer golden-parity harness (enables aggressive token cuts in 79/87/88 with regression safety)
- Issue 89 — A/B harness for build pipeline (cost-lever evaluation on top of 84; benefits from 90's parity net)

### v0.24.0 — Token-cost reduction (gated on v0.23 safety net)

- Issue 87 — `mantle compress` for input-token compression (direct token-cost reduction)
- Issue 79 — audit `.mantle/` + `CLAUDE.md` for progressive-disclosure drift (consider splitting at shape time: mechanical `@file` include refactor vs audit-context CLI)

### v0.25.0 — Workflow-loop efficiency

- Issue 71 — dynamic end-of-command recommendations with fresh-context handoff (absorbed 72)

### v0.26.0+ — Cross-repo expansion

- Issue 85 — schedule shape session within ~2 weeks; GSD env-var → TTY session-identity pattern as lead candidate primitive (don't pre-extract)

### Backlog (unscheduled — revisit after optimisation slice lands)

- Issue 70 — end-of-build triage prompt
- Issue 73 — lightweight bug-fix pipeline
- Issues 66 (worktree), 67 (Jira), 42 (GH report), 86 (external skills), 68 (mantle upgrade), 69 (mantle archive) — deferred unless they surface as blockers

Recently closed:
- Issue 75 → superseded by 84 + new issue 89 (see archive)
- Issue 72 → merged into 71 (see archive)

## Recently Completed

- Issue 44 — Fix hardcoded .mantle/ path reads in Claude Code prompts (approved 2026-04-09)
- Issue 45 — Archive scan in next_issue_number
- Issue 40 — Review feedback loop CLI availability
