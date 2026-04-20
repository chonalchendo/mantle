---
title: Auto-load baseline skills (e.g. python-314) based on project constraints
status: approved
slice:
- core
- cli
story_count: 2
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
- Finnhub Data Source
- Finviz Data Source
- Howard Marks Investment Philosophy
- John Templeton Investment Philosophy
- Lakehouse Architecture
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
- inline-snapshot
- omegaconf
- pydantic-discriminated-unions
- pydantic-project-conventions
- streamlit
- streamlit-aggrid
tags:
- type/issue
- status/approved
acceptance_criteria:
- id: ac-01
  text: Project-level constraint detection parses `requires-python` from
  passes: false
  waived: false
  waiver_reason: null
- id: ac-02
  text: '`mantle update-skills --issue N` unions baseline skills with'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-03
  text: '`mantle compile --issue N` subsequently compiles the baseline skills'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-04
  text: If a baseline skill is named but not present in the vault, emit a
  passes: false
  waived: false
  waiver_reason: null
- id: ac-05
  text: 'Unit tests cover: (a) the `requires-python → baseline` mapping,'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-06
  text: '`CLAUDE.md` / `system-design.md` note the baseline-skills concept'
  passes: false
  waived: false
  waiver_reason: null
---

## Parent PRD

product-design.md, system-design.md

## Why

`mantle update-skills --issue N` auto-detects vault skills by scanning the
issue's body text for matches. Baseline language/runtime skills never get
matched this way because issues rarely mention \"Python 3.14\" explicitly —
yet agents working on any 3.14+ codebase need that knowledge.

Concrete harm seen in issue 58's build pipeline (2026-04-16): the simplifier
agent reverted a previously-committed PEP 758 `except X, Y:` change back to
`except (X, Y):` because it didn't know 3.14 accepts the paren-less form.
The python-314 skill explicitly covers this (\"Do not flag `except A, B:`
as invalid syntax\") but wasn't compiled for the issue because the
auto-matcher never flagged it.

This is a class-of-issue pattern: any agent working on a 3.14+ project can
hit 3.14-specific syntax and make wrong decisions. Same applies to other
language/ecosystem baselines (e.g. `pydantic-project-conventions` on any
Pydantic-heavy project) that should be on by default rather than opted into
via issue wording.

## What to build

A baseline-skills mechanism in `mantle update-skills` that force-includes
certain vault skills based on project constraints, independent of issue
body matching.

### Flow

1. Read `pyproject.toml` (and optionally other manifest files) to extract
   project-level constraints. Minimum viable: parse `requires-python` and
   derive a Python version band (e.g. `>=3.14` → band `3.14`).
2. Resolve a **baseline skill set** for the detected constraints. For
   Python 3.14+: include `python-314` if present in the vault. Policy can
   live in a small config module or in `state.md` under a new
   `baseline_skills:` list seeded on `mantle init`.
3. On `mantle update-skills --issue N`, union the baseline set with the
   auto-detected matches before writing `skills_required`. Auto-detected
   matches stay as they are; baseline skills are always added.
4. Report clearly:
   > Baseline skills (always loaded): python-314
   > Issue-matched skills (from body scan): cyclopts, inline-snapshot
5. The resolved list feeds `mantle compile --issue N` the same way as today,
   so shape/plan/implement/simplify agents all see the baseline skills
   automatically.

## Acceptance criteria

- [ ] ac-01: Project-level constraint detection parses `requires-python` from
- [ ] ac-02: `mantle update-skills --issue N` unions baseline skills with
- [ ] ac-03: `mantle compile --issue N` subsequently compiles the baseline skills
- [ ] ac-04: If a baseline skill is named but not present in the vault, emit a
- [ ] ac-05: Unit tests cover: (a) the `requires-python → baseline` mapping,
- [ ] ac-06: `CLAUDE.md` / `system-design.md` note the baseline-skills concept

## Blocked by

None.

## User stories addressed

- As a Mantle contributor building on a Python 3.14+ project, I want
  language-baseline vault skills to be auto-included in every issue's
  skills_required so that agents don't misdiagnose valid 3.14 syntax as
  errors.
- As a Mantle contributor, I want baseline skills to be explicit and
  inspectable so that surprise omissions don't silently degrade agent
  quality.