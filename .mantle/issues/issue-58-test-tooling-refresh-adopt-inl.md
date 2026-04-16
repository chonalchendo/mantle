---
title: 'Test-tooling refresh: adopt inline_snapshot and dirty-equals, introduce named
  scenario fixtures'
status: implementing
slice:
- tests
- cli
story_count: 1
verification: null
blocked_by: []
skills_required:
- CLI design best practices
- Design Review
- DuckDB Best Practices and Optimisations
- Howard Marks Investment Philosophy
- John Templeton Investment Philosophy
- Mohnish Pabrai Investment Philosophy
- Nick Sleep Investment Philosophy
- OpenRouter LLM Gateway
- Production Project Readiness
- Python 3.14
- Python Project Conventions
- Python package structure
- SQLMesh Best Practices
- Tom Gayner Investment Philosophy
- claude-sdk-structured-analysis-pipelines
- cyclopts
- dirty-equals
- docker-compose-python
- edgartools
- fastapi
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

Mantle's tests currently hand-write expected-output strings for CLI commands
and compiled markdown, and use custom sort-then-compare helpers for
manifests/tags/issue lists where order is incidental. Both habits add
maintenance drag: snapshot strings drift when output formatting changes
(churn with no regression signal), and hand-rolled order-independent
comparisons are noisy at every call site.

Scout analysis of `pydantic/monty` (2026-04-16) surfaced two Pydantic-ecosystem
test tools — `inline_snapshot` and `dirty-equals` — that address these exact
pains, and a fixture-naming convention that makes tests read as specifications
of the vault state they exercise. Adopting them as a pilot (not a full sweep)
compounds into every future issue, especially issue 51 which will migrate
many error paths with associated tests.

## What to build

A pilot adoption that (a) adds the two test dependencies, (b) introduces a
small set of named scenario fixtures, (c) migrates a representative handful
of tests across three scenarios (CLI-output capture, unordered-collection
comparison, scenario-fixture consumption), and (d) documents the conventions
so future tests opt in as they are touched.

### Flow

1. Add `inline-snapshot` and `dirty-equals` to the `check` (test) dependency
   group in `pyproject.toml`; run `uv sync --group check`.
2. Introduce named scenario fixtures in `tests/conftest.py` (e.g.
   `vault_with_issues`, `vault_after_init`) that wrap `tmp_path` with
   pre-built `.mantle/` structures. Docstrings describe the scenario.
3. Migrate ~3-5 representative tests:
   - At least one CLI-output test to `inline_snapshot` (replaces hand-written
     expected strings).
   - At least one unordered-collection test (manifest / tags / issue list) to
     `dirty-equals`.
   - At least one test that consumes a new named scenario fixture.
4. Document the conventions in `CLAUDE.md` under the "Test Conventions"
   section: when to reach for `inline_snapshot` (exact-output capture), when
   for `dirty-equals` (unordered / partial comparison), and the naming
   convention for scenario fixtures.
5. Add a matching one-line mention in `system-design.md`'s "Test Tooling"
   section so the two new helpers are discoverable from the design doc.
6. `just check` passes.

## Acceptance criteria

- [ ] `inline-snapshot` and `dirty-equals` are declared in the `check`
      dependency group in `pyproject.toml` and resolved in `uv.lock`.
- [ ] At least one existing CLI-output test is migrated to `inline_snapshot`,
      with the hand-written expected string removed.
- [ ] At least one existing unordered-collection assertion is migrated to
      `dirty-equals` (e.g. `IsList(..., check_order=False)` or
      `IsPartialDict(...)`), with the custom sort-compare helper removed.
- [ ] At least one named scenario fixture exists in `tests/conftest.py`
      (e.g. `vault_with_issues`, `vault_after_init`) with a docstring
      describing the scenario, and is consumed by at least one test.
- [ ] `CLAUDE.md` Test Conventions section documents: when to use
      `inline_snapshot`, when to use `dirty-equals`, and the scenario-fixture
      naming convention.
- [ ] `system-design.md` Test Tooling section mentions both helpers.
- [ ] `just check` passes.

## Blocked by

None

## User stories addressed

- As a Mantle contributor, I want CLI-output tests to use `inline_snapshot` so
  that expected-output strings are auto-maintained and test failures signal
  real regressions rather than formatting drift.
- As a Mantle contributor, I want order-independent assertions to use
  `dirty-equals` so that insertion order doesn't cause spurious test
  failures.
- As a Mantle contributor, I want named scenario fixtures so that tests read
  as specifications of the vault state they exercise, making the suite
  easier to extend.