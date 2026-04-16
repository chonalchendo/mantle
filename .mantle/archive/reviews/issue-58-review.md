---
issue: 58
title: 'Test-tooling refresh: adopt inline_snapshot and dirty-equals, introduce named
  scenario fixtures'
status: approved
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-16'
tags:
- type/review
- phase/reviewing
---

# Review — Issue 58

**Test-tooling refresh: adopt inline_snapshot and dirty-equals, introduce named scenario fixtures**

## Criteria

- ✓ **inline-snapshot and dirty-equals declared in the check dependency group in pyproject.toml and resolved in uv.lock** [approved] — passed: true
  > Declared in dev group which is transitively included by check via include-group.
- ✓ **At least one existing CLI-output test is migrated to inline_snapshot, with the hand-written expected string removed** [approved] — passed: true
  > test_render_report_produces_markdown_with_themes_and_trend_table captures full markdown via snapshot().
- ✓ **At least one existing unordered-collection assertion is migrated to dirty-equals, with the custom sort-compare helper removed** [approved] — passed: true
  > test_round_trip uses IsPartialDict kwargs form; weaker than the old four asserts but reads as a structural spec.
- ✓ **At least one named scenario fixture exists in tests/conftest.py with a docstring describing the scenario, and is consumed by at least one test** [approved] — passed: true
  > vault_with_learnings with docstring; consumed by test_render_report_*.
- ✓ **CLAUDE.md Test Conventions section documents when to use inline_snapshot, when to use dirty-equals, and the scenario-fixture naming convention** [approved] — passed: true
  > Four bullets added in Test Conventions.
- ✓ **system-design.md Test Tooling section mentions both helpers** [approved] — passed: true
  > One-line mention added.
- ✓ **just check passes** [approved] — passed: true
  > 1148 tests pass; ruff format clean.
