---
issue: 38
title: Fix collect-issue-files commit detection for story commits
approaches:
- Scope-delimited grep — use (issue-N) pattern matching conventional commit scope
- Regex word boundary — use extended-regexp with issue-N followed by non-digit
chosen_approach: Scope-delimited grep — use (issue-N) pattern matching conventional
  commit scope
appetite: small batch
open_questions:
- none
author: 110059232+chonalchendo@users.noreply.github.com
created: '2026-04-07'
updated: '2026-04-07'
updated_by: 110059232+chonalchendo@users.noreply.github.com
tags:
- type/shaped
- phase/shaping
---

## Chosen Approach: Scope-delimited grep

### Problem
`collect_issue_files` uses `--grep=issue-{N}` which is too loose:
- `issue-3` matches `issue-30`, `issue-31`, etc. (partial number match)
- No-commits case raises NoCommitsFoundError instead of returning empty tuple

### Solution
Change git log grep from `--grep=issue-{N}` to `--grep=(issue-{N})` which matches the conventional commit scope format exactly. The parentheses provide natural delimiters that prevent partial matches.

For single-digit issues (1-9), also search with zero-padded variant `(issue-0N)` to catch early commits that used that format.

Change no-commits behaviour from raising NoCommitsFoundError to returning an empty tuple.

### Why not regex word boundary?
`--extended-regexp` with `issue-{N}[^0-9]` fails at end-of-line and requires more complex escaping. The scope delimiter approach is simpler and exactly matches how conventional commits work.

## Code Design

### Strategy
Modify `simplify.collect_issue_files()` in `src/mantle/core/simplify.py`:
1. Build grep patterns: `(issue-{N})` primary, `(issue-0{N})` secondary for N<10
2. Run git log with each pattern, merge results
3. Return empty tuple instead of raising when no commits found

Remove `NoCommitsFoundError` (dead code after this change).
Update CLI layer `src/mantle/cli/simplify.py` to handle empty tuple instead of catching exception.

### Fits architecture by
- Change is entirely in core/ and cli/ layers — respects core-never-imports-cli boundary
- Uses existing subprocess git pattern already established in simplify.py
- Follows conventional commit format that implement.md enforces

### Does not
- Does not change commit message format (that's the implement command's responsibility)
- Does not add new dependencies
- Does not change collect_changed_files (unrelated function)
- Does not handle non-conventional commit formats (those are pipeline metadata, not implementation)