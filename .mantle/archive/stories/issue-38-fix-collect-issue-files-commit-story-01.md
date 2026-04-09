---
issue: 38
title: Fix commit pattern matching and graceful empty return
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As the build pipeline's simplification step, I want collect-issue-files to accurately find story commits and return empty gracefully so that file counting works correctly.

## Depends On

None — independent (single story).

## Approach

Fix the two bugs in `simplify.collect_issue_files()`: tighten the git grep pattern to use conventional commit scope delimiters `(issue-N)` preventing partial number matches, and return an empty tuple instead of raising when no commits exist. Update CLI layer to handle the new return type. Update tests to cover both fixes.

## Implementation

### src/mantle/core/simplify.py (modify)

1. **Remove `NoCommitsFoundError`** — no longer needed since no-commits returns empty tuple.

2. **Fix `collect_issue_files` grep pattern:**
   - Change `--grep=issue-{issue}` to `--grep=(issue-{issue})`
   - This matches the conventional commit scope format exactly: `feat(issue-38):`, `fix(issue-38):`, etc.
   - The parentheses act as natural delimiters preventing `issue-3` from matching `issue-30`
   - For single-digit issues (N < 10), run a second git log with `--grep=(issue-0{N})` to catch zero-padded commits from early project history (e.g., `feat: add session logging (issue-09)`)
   - Merge commit hashes from both queries

3. **Graceful empty return:**
   - When no commits found, return empty `()` instead of raising `NoCommitsFoundError`
   - When only one commit found, use `{commit}^..{commit}` range (existing logic handles this)

### src/mantle/cli/simplify.py (modify)

1. **Update `run_collect_issue_files`:**
   - Remove the `try/except NoCommitsFoundError` block
   - Check if returned tuple is empty; if so, print a user-friendly message and return (no SystemExit)
   - Print file count summary after listing files

#### Design decisions

- **Scope-delimited pattern over regex**: `(issue-N)` is simpler than `--extended-regexp` with `[^0-9]` and naturally handles end-of-line
- **Zero-pad only for N<10**: Issue numbers 10+ were never zero-padded in this project's history
- **Remove exception class**: Dead code after this change; keeping it would violate YAGNI

## Tests

### tests/core/test_simplify.py (modify)

- **test_finds_matching_commits**: Keep existing — already uses `feat(issue-1):` format which contains `(issue-1)`
- **test_no_commits_returns_empty**: Replace `test_no_commits_raises` — verify returns `()` instead of raising
- **test_excludes_partial_number_match**: New — create commits for issue-3 and issue-30, collect issue-3, verify issue-30 files excluded. This is the core regression test.
- **test_finds_zero_padded_commits**: New — create commit with `feat(issue-01):` message, collect issue 1, verify file found
- **test_excludes_other_issues**: Keep existing — already validates cross-issue isolation

### tests/cli/test_simplify.py (modify)

- **test_no_commits_prints_message**: Update to verify graceful output (no SystemExit) when no commits found