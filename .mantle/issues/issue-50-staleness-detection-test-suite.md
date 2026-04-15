---
title: Staleness detection test suite — compile-modify-recompile regression tests
status: verified
slice:
- core
- cli
- tests
story_count: 1
verification: null
blocked_by: []
skills_required:
- CLI design best practices
- Design Review
- Python package structure
- SQLMesh Best Practices
- cyclopts
- docker-compose-python
- edgartools
- fastapi
- omegaconf
- pydantic-project-conventions
- streamlit
- streamlit-aggrid
tags:
- type/issue
- status/verified
---

## Parent PRD

product-design.md, system-design.md

## Why

Side-effect ordering bugs are the project's most recurring failure pattern. Three learnings (issues 46, 47, 49) and two inbox bugs describe the same class of problem: commands fail because prior commands archived or moved files unexpectedly, and downstream commands can no longer find them. Current unit tests don't exercise multi-step sequences where one command's side effects affect another.

Colin's staleness detection testing pattern (compile, modify source, compile again — verify only changed documents recompile and no orphaned artifacts remain) demonstrates how to catch this class of bug systematically.

## What to build

A regression test suite that exercises multi-step command sequences, focusing on three areas:

1. **Compile lifecycle tests** — create, modify, and delete skills/tags, then run `mantle compile` and verify indexes are created, updated, and orphaned indexes are cleaned up.
2. **CLI command ordering tests** — verify that `save-review-result` succeeds when called before `transition-issue-approved`, and fails gracefully (not silently) if called after archival.
3. **Archive side-effect tests** — verify that `find_issue_path` and downstream commands (save-review-result, save-learning, update-story-status) work correctly after `archive_issue` runs, or raise clear errors if the file has moved.

### Flow

1. Each test creates a realistic `.mantle/` fixture in `tmp_path` with issues, stories, and skills
2. Test runs the first command in the sequence (e.g., compile, transition-issue-approved)
3. Test modifies state (e.g., rename a tag, archive an issue)
4. Test runs the second command and asserts correct behaviour (updated output, graceful error, no orphaned files)

## Acceptance criteria

- [ ] Compile-modify-recompile tests exist for `mantle compile` — verify new indexes created, modified indexes updated, orphaned indexes deleted
- [ ] CLI ordering tests verify `save-review-result` succeeds when called before `transition-issue-approved` (and fails gracefully if called after)
- [ ] Archive side-effect tests verify `find_issue_path` and downstream commands work correctly after `archive_issue` runs
- [ ] All tests use `tmp_path` isolation with realistic `.mantle/` fixtures (no real vault)
- [ ] `just check` passes with the new test suite

## Blocked by

None

## User stories addressed

- As a maintainer, I want regression tests that catch side-effect ordering bugs before they reach human review, so that the recurring pattern from issues 46, 47, and 49 doesn't repeat.
- As a developer adding new CLI commands, I want existing ordering tests to verify my new command doesn't break the multi-step workflow, so that I catch integration issues during development.