---
issue: 58
title: 'Test-tooling refresh: adopt inline_snapshot and dirty-equals, introduce named
  scenario fixtures'
approaches:
- Single vertical slice
- Layered (deps then migration)
- Full sweep
chosen_approach: Single vertical slice
appetite: small batch
open_questions:
- None — scope was settled at add-issue; shaping only confirmed test targets.
author: 110059232+chonalchendo@users.noreply.github.com
created: '2026-04-16'
updated: '2026-04-16'
updated_by: 110059232+chonalchendo@users.noreply.github.com
tags:
- type/shaped
- phase/shaping
---

## Approaches considered

### A. Single vertical slice (chosen, small batch)

One PR: deps + conftest fixture + two representative migrations + doc
updates. Already scoped tight in add-issue; the pilot exists to prove the
conventions before broader migration, so splitting has no payoff.

### B. Layered: deps and fixtures first, migration second (medium batch)

Separate PR for scaffolding (deps, conftest fixture) then a follow-up PR
for the test migrations. Adds two-PR drag with no gain — the deps are
trivial to land and the migrations are what validate the conventions.

### C. Full sweep (large batch)

Migrate every eligible test in one go. Explicitly rejected at add-issue
time (scout directive: pilot, not sweep).

## Chosen approach: Single vertical slice

Smallest appetite that satisfies all acceptance criteria. The ACs already
demand only one inline_snapshot migration, one dirty-equals migration,
one fixture, and doc updates.

## Code design

### Strategy

- **pyproject.toml**: add `inline-snapshot` and `dirty-equals` to the
  `[dependency-groups].dev` group (transitively included in `check` via
  `include-group = "dev"`). Run `uv sync --group check` to update lock.
- **tests/conftest.py** (new file, top-level): export a named scenario
  fixture `vault_with_learnings(tmp_path) -> Path` that builds
  `.mantle/learnings/` + `.mantle/issues/` with 2 learnings (core/+1
  testing-woes, cli/-1 worktree-trouble) + matching issues. Docstring:
  *\"Vault state with a core/testing learning (+1) and a cli/worktree
  learning (-1), each with a matching issue file — the canonical scenario
  for pattern/theme rendering tests.\"* The existing `_write_learning` /
  `_write_issue` helpers in `tests/core/test_patterns.py` move into
  conftest as module-private helpers used by the fixture.
- **tests/core/test_patterns.py::test_render_report_produces_markdown_with_themes_and_trend_table**:
  consume the `vault_with_learnings` fixture. Replace ~10 `assert X in
  rendered` calls with one `assert rendered == snapshot(\"\"\"...\"\"\")`
  capturing the full markdown. This single migrated test satisfies both
  the inline_snapshot AC and the scenario-fixture consumption AC.
- **tests/core/test_learning.py::TestSaveLearning::test_round_trip**:
  replace the 4 attribute-by-attribute `assert loaded_note.X ==
  saved_note.X` lines with one `assert loaded_note.model_dump() ==
  IsPartialDict({...})` — demonstrates dirty-equals tolerating the stable
  vs. unstable-field split (author/date can be matched loosely, content
  stays exact).
- **CLAUDE.md** Test Conventions: append a 4-bullet block —
  (a) inline_snapshot for exact-string capture (CLI output, rendered
  markdown); (b) dirty-equals for partial/unordered comparison
  (`IsPartialDict`, `IsList(check_order=False)`); (c) scenario-fixture
  naming `vault_with_<state>` / `<noun>_after_<event>`; (d) don't mix
  the two — inline_snapshot captures values, dirty-equals captures shape.
- **system-design.md** Test Tooling section: one line —
  *\"`inline_snapshot` and `dirty-equals` are available for exact-output
  capture and structural comparison respectively.\"*

### Fits architecture by

- `tests/conftest.py` is the canonical pytest location for cross-suite
  fixtures (there was none prior).
- Applies skill conventions directly: inline_snapshot §\"Named scenario
  fixtures pattern\" (one fixture = one scenario = one snapshot);
  dirty-equals §\"partial-vs-exact dict\" (replace attribute-by-attribute
  with `IsPartialDict`).
- Python-project-conventions: `check` group already includes `dev` via
  `include-group`, so test-only deps go in `dev` and transitively satisfy
  the \"in check group\" acceptance criterion.
- Does not cross the `core` never imports `cli` boundary — pure
  test-layer change.

### Does not

- Does not migrate beyond 1 inline_snapshot test + 1 dirty-equals test.
  Pilot, not sweep.
- Does not rewrite existing `_write_learning` / `_write_issue` helpers in
  remaining `test_patterns.py` tests — only the migrated test consumes
  the fixture; others keep their current helpers until a future sweep.
- Does not reconfigure pytest collection, console geometry, or
  `[tool.inline-snapshot]` pyproject options beyond defaults.
- Does not migrate `tests/cli/test_help_groups.py` (inline_snapshot
  candidate but structurally different — out of scope).
- Does not extend the fixture beyond the two-learning scenario.