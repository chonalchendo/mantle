---
issue: 50
title: Staleness detection test suite
approaches:
- A. Single regressions module — one new tests/test_staleness_regressions.py with
  three TestClass groupings (compile lifecycle, CLI ordering, archive side-effects)
  plus a shared fixture helper. Small batch.
- B. Three mirrored test modules — tests/core/test_compile_lifecycle.py, tests/cli/test_command_ordering.py,
  tests/core/test_archive_side_effects.py. Follows existing mirror layout; ~3x more
  files. Small-medium batch.
- C. Shared fixture-factory library + thin tests — build tests/_fixtures/mantle_factory.py
  reusable across the project, then thin per-area test modules. Higher upfront cost,
  dividends across future tests. Medium batch.
chosen_approach: A. Single regressions module
appetite: small batch
open_questions:
- What is the desired (vs. current) failure mode for save-review-result called after
  issue archival? Test will assert observed behaviour and may surface a follow-up
  bug.
author: 110059232+chonalchendo@users.noreply.github.com
created: '2026-04-15'
updated: '2026-04-15'
updated_by: 110059232+chonalchendo@users.noreply.github.com
tags:
- type/shaped
- phase/shaping
---

## Why

Side-effect ordering bugs are the project's most recurring failure pattern (issues 46/47/49 + 2 inbox bugs). Current unit tests exercise commands in isolation; this suite exercises the multi-step sequences where one command's side effects affect another.

## Approaches considered

### A. Single regressions module (CHOSEN)
One new `tests/test_staleness_regressions.py` at the top level with three `TestClass` groups:
- `TestCompileLifecycle` — create/modify/delete skills then compile, verify indexes created/updated/orphans cleaned.
- `TestCommandOrdering` — `save-review-result` ordered relative to `transition-issue-approved`.
- `TestArchiveSideEffects` — `find_issue_path` and downstream commands behave correctly after `archive_issue`.

Plus a small in-file `_make_mantle_fixture(tmp_path)` helper that scaffolds a realistic `.mantle/` (state.md, issues/, stories/, skills) for reuse across the three classes.

**Appetite:** small batch (1-2 days, single PR).
**Tradeoff:** one file holds the cross-cutting regression suite — easy to find, easy for future contributors to extend.
**Rabbit hole:** fixture builder bloats if every test wants a different shape. Mitigate by keeping the helper minimal (writes baseline `.mantle/`; tests add what they need).
**No-go:** does not refactor existing per-module tests.

### B. Three mirrored test modules
Split each AC into its own file under `tests/core/` and `tests/cli/` matching the module-mirror convention. Cleaner separation, but the regressions are workflow-level (cross-module) so they don't naturally belong to a single source module. ~3x file count for the same coverage.

### C. Shared fixture factory + thin tests
Build a reusable `tests/_fixtures/mantle_factory.py` library. Higher upfront investment; pays off only if future tests adopt it. YAGNI for a single-issue scope.

## Why A wins

- Matches the work: regression tests are cross-module, so a top-level workflow file is the right home (CLAUDE.md already names this slot).
- Smallest appetite that satisfies all 3 ACs.
- Lowest churn — one file added, no reorganisation.
- Easiest future contribution: when a new side-effect bug is found, add a test class to the same file.

## Code design

### Strategy
Add `tests/test_staleness_regressions.py` with:

```python
def _make_mantle_fixture(tmp_path: Path, *, issues=(), stories=(), skills=()) -> Path:
    """Scaffold .mantle/ + ~/vault/ baseline. Returns the .mantle path."""
    # writes state.md, issues/<n>-*.md, stories/, skills as requested

class TestCompileLifecycle:
    def test_compile_creates_index_for_new_skill(self, tmp_path): ...
    def test_compile_updates_index_when_skill_modified(self, tmp_path): ...
    def test_compile_deletes_orphaned_index_when_skill_removed(self, tmp_path): ...

class TestCommandOrdering:
    def test_save_review_result_succeeds_before_transition_approved(self, tmp_path): ...
    def test_save_review_result_after_archival_fails_gracefully(self, tmp_path): ...

class TestArchiveSideEffects:
    def test_find_issue_path_after_archive(self, tmp_path): ...
    def test_save_learning_after_archive_resolves_archived_path(self, tmp_path): ...
    def test_update_story_status_after_archive_behaves(self, tmp_path): ...
```

Each test:
1. Uses `_make_mantle_fixture(tmp_path, ...)`.
2. Runs first command (via `mantle.cli` entry point or `core` function call).
3. Mutates state.
4. Runs second command and asserts on filesystem + return code.

Use `subprocess.run([sys.executable, '-m', 'mantle', ...], cwd=tmp_path)` for true end-to-end CLI sequencing where ordering matters; fall back to direct `core.*` calls when only the side-effect API needs exercising. Pick subprocess for the CLI-ordering tests — that's where the bugs lived.

### Fits architecture by
- Top-level `tests/test_*.py` slot already documented in `CLAUDE.md` for project-wide tests.
- Uses `tmp_path` per CLAUDE.md test conventions; no real `~/.claude/` or vault touched.
- Calls real CLI via subprocess (matches the live-E2E pattern from issue 46's learning).
- Imports `mantle.core.*` modules directly when not testing CLI surface.
- No new core modules — pure additive test infrastructure.

### Does not
- Does not modify any production code (test-only PR).
- Does not refactor existing tests.
- Does not introduce a fixture-factory library (Approach C explicitly out of scope).
- Does not test commands not named in the ACs.
- Does not assert on the *content* of orphan-cleanup logs — only that orphans are removed.
- Does not introduce a custom pytest plugin or new conftest entries.

## Open questions
- For "fails gracefully if called after archival", what's the desired exit behaviour today — exit code 1 with a message, or exception? Test will assert current behaviour and document it; if the answer is "silent success" the test will fail and a follow-up bug should be filed (per build pipeline guidance: don't ramble — file separately).