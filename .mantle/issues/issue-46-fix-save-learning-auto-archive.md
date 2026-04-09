---
title: Fix save-learning auto-archive breaking /mantle:build pipeline
status: verified
slice:
- core
- tests
story_count: 1
verification: null
blocked_by: []
skills_required:
- CLI design best practices
- Design Review
- Designing Architecture
- DuckDB Best Practices and Optimisations
- DuckLake
- Earnings Transcript Data Sources
- Lakehouse Architecture
- Medallion Architecture & Star Schema
- Mohnish Pabrai Investment Philosophy
- OpenRouter LLM Gateway
- Production Project Readiness
- Python Project Conventions
- Python package structure
- SQLMesh Best Practices
- Software Design Principles
- Tom Gayner Investment Philosophy
- claude-sdk-structured-analysis-pipelines
- cyclopts
- docker-compose-python
- edgartools
- fastapi
- omegaconf
- pydantic-discriminated-unions
- pydantic-project-conventions
- streamlit
- streamlit-aggrid
tags:
- type/issue
- status/verified
---

## Parent PRD

product-design.md, system-design.md

## Why

`mantle save-learning` currently triggers `archive_issue` as a side effect, moving the issue file, shaped doc, and every story file into `.mantle/archive/` the moment it is called. This breaks `/mantle:build` because `implement.md` Step 9 saves a learning mid-pipeline — before `build.md` Steps 7 (simplify) and 8 (verify) have run. Every `/mantle:build` run therefore silently archives files that later steps still need to read, forcing manual `git checkout` recovery to continue.

Observed on two consecutive builds (issues 44 and 45) on 2026-04-09. Two reproductions on two different issues confirms this is a systematic break, not a fluke. It also makes `/mantle:build` unsafe to run unattended — the user must babysit every run to restore files mid-pipeline.

Related inbox items (deduplicate when shaping): `bug-mantle-save-learning-aggre.md` and `save-learning-auto-archive-bre.md` are the same bug filed on consecutive builds.

## What to build

Decouple learning capture from archival. Archiving should only happen on explicit issue transition to a terminal status (e.g. `transition-issue-verified` or the archive command), never as a side effect of capturing a learning.

Approaches to evaluate at shape time:

- (a) Remove the archive call from `save-learning` entirely. Drive archival from the existing verified-transition path only. Cleanest, preserves single responsibility.
- (b) Add a `--no-archive` flag to `save-learning` and have `build.md`/`implement.md` pass it during mid-pipeline captures. Pragmatic but leaves the footgun in place.
- (c) Gate the archive call on \"all stories complete AND issue status == verified\". Hides the coupling instead of removing it.

Default preference: (a). Confirm at shape time.

### Flow

1. Build pipeline or user calls `mantle save-learning` during or after implementation.
2. The learning is persisted to the configured location.
3. No files are moved, archived, or deleted as a side effect.
4. Archiving continues to happen via the existing explicit transition commands, after verification completes.

## Acceptance criteria

- [ ] Calling `mantle save-learning` mid-pipeline does not move any issue, shaped, or story files.
- [ ] A full `/mantle:build` run (shape → plan-stories → implement → simplify → verify) completes end-to-end with no manual file restoration required.
- [ ] Archiving still happens via the documented verified-transition flow — terminal issues still end up in `.mantle/archive/`.
- [ ] A regression test reproduces the mid-pipeline scenario and asserts no files move when `save-learning` is called before verification.
- [ ] Existing `save-learning` and archive tests still pass.
- [ ] `implement.md` Step 9 no longer requires a workaround comment about archival ordering.

## Blocked by

None

## User stories addressed

- As a mantle user running `/mantle:build`, I want learning capture to be free of side effects so that the pipeline can record insights mid-flow without destroying the files later steps need to read.
- As a mantle maintainer, I want archival to happen at exactly one well-defined point (verified transition) so that file state is predictable across the build pipeline.