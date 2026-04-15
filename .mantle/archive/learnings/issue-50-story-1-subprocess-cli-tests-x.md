---
issue: 50
title: 'story-1: subprocess CLI tests + xfail-known-bugs'
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-15'
confidence_delta: '+1'
tags:
- type/learning
- phase/reviewing
---

## Patterns

- Use `[\"uv\", \"run\", \"mantle\", ...]` for subprocess CLI tests, not `[\"mantle\", ...]` or `[sys.executable, \"-m\", \"mantle\", ...]`. The package has no `__main__`; matches `tests/test_package.py`. Avoids installed-vs-working-tree divergence (issue-46 learning).
- Compile-lifecycle tests can call `skills.generate_index_notes()` directly — keeps the fixture minimal vs. invoking the full `mantle compile` CLI.
- xfail surfaced a real bug: `save-learning` never validates issue existence and silently writes after archival. Filed as inbox item — separate fix.

## Wrong assumptions in the build context

- Briefing claimed issue-49 left orphan-index cleanup unimplemented. Wrong — `generate_index_notes` at `src/mantle/core/skills.py:930-939` does cleanup. Test passes outright. Future build contexts should grep before assuming a learning generalises.

## Gotcha

- 4 unrelated source files have pre-existing ruff-format drift; `just check` will fail on format step until that's addressed separately.