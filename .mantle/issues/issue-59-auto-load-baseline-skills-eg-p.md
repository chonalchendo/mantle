---
title: Auto-load baseline skills (e.g. python-314) based on project constraints
status: implementing
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
- status/implementing
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

- [ ] Project-level constraint detection parses `requires-python` from
      `pyproject.toml`; Python 3.14+ produces a `python-314` baseline entry
      when the skill exists in the vault.
- [ ] `mantle update-skills --issue N` unions baseline skills with
      auto-detected skills; baseline entries appear in `skills_required`
      even when the issue body does not mention Python.
- [ ] `mantle compile --issue N` subsequently compiles the baseline skills
      into `.claude/skills/` alongside issue-matched ones.
- [ ] If a baseline skill is named but not present in the vault, emit a
      one-line warning and continue — do not hard-fail.
- [ ] Unit tests cover: (a) the `requires-python → baseline` mapping,
      (b) the union behaviour in `update-skills`, (c) the missing-skill
      warning path.
- [ ] `CLAUDE.md` / `system-design.md` note the baseline-skills concept
      in the skills section.

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