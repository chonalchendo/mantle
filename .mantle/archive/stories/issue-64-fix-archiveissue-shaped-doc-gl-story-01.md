---
issue: 64
title: Widen shaped-doc glob + regression test for slug-less form
status: planned
failure_log: null
tags:
- type/story
- status/planned
---

## Story

Widen the shaped-doc glob in `core/archive.py` so `archive_issue` also matches slug-less shaped filenames (`issue-NN-shaped.md`) in addition to the slugged form. Add a regression test covering the slug-less form and verify the existing slugged-form test still passes.

## Acceptance criteria

- [ ] `archive_issue` matches `issue-NN-shaped.md` (no slug) in addition to `issue-NN-<slug>-shaped.md`.
- [ ] Unit test covers both filename forms; regression test for the slug-less form passes.
- [ ] `just check` passes.

## TDD test specifications

### Test 1 — slug-less shaped doc is archived (new, red → green)

**File:** `tests/core/test_archive.py`
**Test class:** `TestArchiveIssue`
**Test name:** `test_slug_less_shaped_doc_is_archived`

**Setup:** Create a `.mantle/` with an issue file `issue-24-slug-less.md` and a shaped file `issue-24-shaped.md` (no slug) under `.mantle/shaped/`. No stories, no learning.

**Action:** Call `archive.archive_issue(tmp_path, 24)`.

**Assertions:**
- The returned list has length 2 (issue + shaped).
- `.mantle/archive/shaped/issue-24-shaped.md` exists.
- `.mantle/shaped/issue-24-shaped.md` no longer exists.

This test MUST fail against the current code (which uses `issue-{NN:02d}-*-shaped.md`) and pass after widening the glob.

### Test 2 — existing slugged form still works (regression guard)

The existing `test_moves_all_artifacts` already covers the slugged form (`issue-01-test-issue-shaped.md`). No change needed — just re-run it after the fix to prove no regression.

## Implementation plan

1. In `src/mantle/core/archive.py` line 46, change:
   `shaped_dir.glob(f"issue-{issue:02d}-*-shaped.md")`
   to:
   `shaped_dir.glob(f"issue-{issue:02d}*-shaped.md")`
2. Add `test_slug_less_shaped_doc_is_archived` to `tests/core/test_archive.py::TestArchiveIssue` following the spec above.
3. Run `uv run pytest tests/core/test_archive.py -q` locally to confirm both tests pass.
4. Run `just check` to confirm lint/type/format gates pass.

## Out of scope

- Refactoring other parts of `archive.py`.
- Changing the filename convention for shaped docs.
- Adding a helper function — the fix is a single-character glob widening.

## Files touched

- `src/mantle/core/archive.py` (1 line)
- `tests/core/test_archive.py` (1 new test method)