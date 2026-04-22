---
title: Make collect-issue-diff-stats source/test paths configurable for non-src/tests
  projects
status: approved
slice:
- core
- cli
- tests
story_count: 1
verification: null
blocked_by: []
skills_required:
- CLI design best practices
- Python package structure
- cyclopts
- edgartools
- fastapi
- omegaconf
- pydantic-project-conventions
- python-314
- streamlit-aggrid
tags:
- type/issue
- status/approved
acceptance_criteria:
- id: ac-01
  text: '`config.md` accepts a structured field declaring which paths count as source,
    test, and optionally other categories.'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-02
  text: '`collect-issue-diff-stats` reads that config and categorises changed files
    accordingly; unclassified files are reported under an "other" bucket rather than
    silently dropped.'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-03
  text: When the config field is absent, behaviour matches today (`src/` = source,
    `tests/` = test).
  passes: false
  waived: false
  waiver_reason: null
- id: ac-04
  text: A dbt-style fixture (models/, tests/, macros/) produces sensible stats in
    a test.
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

`mantle collect-issue-diff-stats` hardcodes `src/` and `tests/` as the source and test roots. That's correct for this repo but breaks on projects with other layouts — dbt (`models/`, `tests/`, `seeds/`, `macros/`), frontend repos (`app/`, `components/`, `__tests__/`), monorepos, etc. Blocks onboarding Mantle to the user's work projects.

## What to build

A configurable path mapping so projects can declare which trees count as source, test, and optionally other categories (e.g. docs, fixtures). Likely lives in `config.md` alongside `verification_strategy` — one new field like `diff_paths:` with a small schema.

Keep the current defaults (`src/`, `tests/`) so existing projects are unchanged. When the config field is present, use it; when absent, fall back to defaults.

## Acceptance criteria

- [ ] ac-01: `config.md` accepts a structured field declaring which paths count as source, test, and optionally other categories.
- [ ] ac-02: `collect-issue-diff-stats` reads that config and categorises changed files accordingly; unclassified files are reported under an "other" bucket rather than silently dropped.
- [ ] ac-03: When the config field is absent, behaviour matches today (`src/` = source, `tests/` = test).
- [ ] ac-04: A dbt-style fixture (models/, tests/, macros/) produces sensible stats in a test.
- [ ] ac-05: `just check` passes.

## Blocked by

None

## User stories addressed

- As a Mantle user adopting the tool on a dbt project, I want diff stats to classify dbt folders correctly so the build pipeline's mechanical-vs-logic signals still work.
- As a maintainer, I want the path mapping to live in config.md so introspection and diff stats share one source of truth.