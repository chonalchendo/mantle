---
issue: 57
story: 1
title: Fail loudly when save-learning targets an unknown or archived issue
status: planned
estimated_effort: small
tags:
  - type/story
  - status/planned
---

## Goal

Make `mantle save-learning --issue NN` fail with a clear error and
non-zero exit when issue NN is not present in `.mantle/issues/`
(including when it has been archived), instead of silently writing a
learning file with no live issue to link back to.

## Context

From the shape doc
(`.mantle/shaped/issue-57-save-learning-silently-writes-shaped.md`):
chosen approach is **strict** — raise on precondition failure in
`core.learning.save_learning`, catch in `cli.learning`, exit 1 with an
actionable message.

## Test specifications (TDD — write these first)

1. **`tests/core/test_learning.py`** — new test
   `test_save_learning_raises_when_issue_missing`:
   - Build a minimal `.mantle/` under `tmp_path` with no issues.
   - Call `learning.save_learning(tmp_path, "body", issue=99,
     title="t", confidence_delta="+1")`.
   - Assert it raises `learning.IssueNotFoundError`.
   - Assert no file was created under
     `tmp_path / ".mantle" / "learnings"`.

2. **`tests/core/test_learning.py`** — new test
   `test_save_learning_raises_when_issue_archived`:
   - Fixture with issue 50 present, then call
     `archive.archive_issue(tmp_path, 50)`.
   - Call `save_learning` targeting issue 50.
   - Assert `IssueNotFoundError` is raised and no learning file
     exists.

3. **`tests/test_staleness_regressions.py`** — remove the
   `@pytest.mark.xfail(...)` decorator on
   `test_save_learning_after_archive_fails_clearly`. It should now
   pass as a real assertion.

4. **Happy path regression** — existing
   `test_learning.py` tests that cover successful save continue to
   pass unchanged (the precondition must not fire when the issue
   exists).

## Implementation steps

1. In `src/mantle/core/learning.py`:
   - Add `IssueNotFoundError` exception class near
     `LearningExistsError`.
   - Import `issues` (already imported at module top).
   - In `save_learning`, immediately after
     `_validate_confidence_delta(confidence_delta)`, add:
     ```python
     if issues.find_issue_path(project_dir, issue) is None:
         raise IssueNotFoundError(issue)
     ```
   - Update the docstring `Raises:` section to list the new error.
2. In `src/mantle/cli/learning.py`:
   - Add an `except learning.IssueNotFoundError as exc:` branch to
     the existing try/except that prints an actionable message to
     stderr and exits 1.
3. Run `uv run pytest tests/core/test_learning.py
   tests/test_staleness_regressions.py -x` until green.
4. Run `just check`.

## Acceptance criteria

- [ ] `IssueNotFoundError` exists in `mantle.core.learning` with
      an informative `__str__` referencing the issue number and the
      archive possibility.
- [ ] `save_learning` raises `IssueNotFoundError` when the issue is
      absent from `.mantle/issues/`; no filesystem writes occur.
- [ ] CLI prints a clear, actionable error to stderr and exits with
      code 1 in that scenario.
- [ ] `test_save_learning_after_archive_fails_clearly` is a real
      passing test (no `xfail` marker).
- [ ] All existing learning tests still pass.
- [ ] `just check` passes.

## Out of scope

- Permissive annotation mode (option 2 in the shape doc).
- Touching other commands in the same staleness family (handled by
  issues 46/47/49/56).
