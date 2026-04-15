---
title: save-learning silently writes after issue archived
status: implementing
slice:
- core
- cli
story_count: 0
verification: null
blocked_by: []
skills_required:
- CLI design best practices
- Design Review
- Software Design Principles
- cyclopts
tags:
- type/issue
- status/implementing
---

## Parent PRD

product-design.md, system-design.md

## Why

`mantle save-learning --issue NN` silently succeeds when issue NN has been archived. The CLI writes a learning file to `.mantle/learnings/` even though `find_issue_path` returns None for the issue, so the resulting learning has no live issue to link back to. This is a side-effect-ordering bug in the same family as issues 46, 47, and 49.

Discovered by `tests/test_staleness_regressions.py::TestArchiveSideEffects::test_save_learning_after_archive_fails_clearly` (currently `xfail` with strict=False; will flip to a real pass once fixed).

## What to build

Modify `mantle.core.learning.save_learning` (and its CLI shim in `mantle.cli.learning`) so that when the target issue cannot be found in either `.mantle/issues/` or `.mantle/archive/issues/`, the call fails with a clear message rather than silently writing.

Two behaviour options to evaluate during shaping:

1. **Strict — fail loudly when issue is not in `.mantle/issues/`.** Treats any post-archive save-learning as an error. Simpler, matches the spirit of the existing `find_issue_path` contract.
2. **Permissive — look up the archived issue path and annotate the learning.** Lets retrospectives run after archival, but adds an `archived_issue_path` field to the learning frontmatter so consumers know the issue is no longer live.

Pick the option during shaping; both close the silent-success bug.

## Acceptance criteria

- [ ] `mantle save-learning --issue NN` exits non-zero and prints a clear error when issue NN is not found in `.mantle/issues/` (option 1) OR succeeds with archived-issue annotation (option 2 — picked during shaping).
- [ ] `tests/test_staleness_regressions.py::TestArchiveSideEffects::test_save_learning_after_archive_fails_clearly` flips from xfail to a real pass (or is updated to match option 2's contract and still passes).
- [ ] Existing learning tests still pass.
- [ ] `just check` passes.

## Blocked by

None.

## User stories addressed

- As a maintainer, I want save-learning to refuse to write a learning for an issue that has been archived, so that learnings always link to a discoverable issue.