---
issue: 63
title: Default-filter collect_issue_diff_stats to src/+tests/ and align build.md Step
  7
status: in-progress
failure_log: null
tags:
- type/story
- status/in-progress
---

## User Story

As a Mantle user running `/mantle:build` on an issue whose diff is mostly `.md` prose, I want the simplify gate to skip correctly rather than spawn a refactorer agent with nothing in-scope to simplify, so the pipeline's cost matches the work it can actually perform.

## Depends On

None — independent (only story in issue 63).

## Approach

Make `src/mantle/core/simplify.py::collect_issue_diff_stats` filter its `git diff --shortstat` call to the `src/` and `tests/` pathspec by default. This aligns the stats source with the simplifier's own scope in `claude/commands/mantle/build.md` Step 7 — both now reference the same `src/ tests/` paths. The CLI command signature is unchanged (no new flag; YAGNI per the shaped doc's grep evidence — Step 7 is the only caller). Follows the same codebase pattern as the existing `collect_issue_diff_stats` — add a pathspec to the existing `subprocess.run` `git diff` invocation.

## Implementation

### `src/mantle/core/simplify.py` (modify)

Locate `collect_issue_diff_stats` (≈ line 162). Change the `subprocess.run` call from:

```python
shortstat = subprocess.run(
    ["git", "diff", "--shortstat", f"{first_commit}^..{last_commit}"],
    capture_output=True,
    text=True,
    check=True,
    cwd=project_root,
)
```

to:

```python
shortstat = subprocess.run(
    [
        "git", "diff", "--shortstat",
        f"{first_commit}^..{last_commit}",
        "--", "src/", "tests/",
    ],
    capture_output=True,
    text=True,
    check=True,
    cwd=project_root,
)
```

Update the function's docstring to document the scope:
- Add to the description: "Counts only changes in `src/` and `tests/` — aligns with the simplifier's edit scope in `/mantle:build` Step 7."
- Note in the Returns section: `DiffStats(0, 0, 0, 0)` is returned both when no matching commits exist AND when matching commits exist but touch only paths outside `src/`+`tests/`.

Do not modify `collect_issue_files` — that function has different callers and a different responsibility (reporting all changed files for the simplifier's in-scope listing happens separately via the build.md `git diff --name-only` line).

### `claude/commands/mantle/build.md` (modify)

In Step 7, immediately after the "Skip condition" paragraph (around line 311–315), clarify the alignment. Leave the thresholds and skip prose intact, but make the scope alignment explicit. Either:

- Replace the parenthetical in the file-list-capture paragraph (currently `(Use the PRE_IMPLEMENT_REV recorded at the start of Step 6. Filter to src/ and tests/ to exclude .mantle/ churn from auto-commits, which is never simplifier territory.)`) with a version that notes `collect-issue-diff-stats` uses the identical `-- src/ tests/` pathspec, OR
- Add a single sentence after the skip-condition prose: "The stats command counts only `src/` and `tests/` paths — the same pathspec used below to produce the file list."

Prefer the second option (smaller edit, leaves existing explanatory prose intact). Do not change the `git diff --name-only $PRE_IMPLEMENT_REV..HEAD -- src/ tests/` line — that still produces the file list the agent needs.

#### Design decisions

- **Default-filter vs `--scope` flag**: shaped doc (issue-63-shaped.md) chose default-filter. Grep evidence confirmed Step 7 is the only caller. Adding a flag for a nonexistent caller is YAGNI (`cli-design-best-practices`).
- **Don't touch `collect_issue_files`**: different responsibility. Out of scope for issue 63.
- **Keep the thresholds unchanged** (`files ≤ 3` AND `lines_changed ≤ 50`): the alignment problem is about what the stats count, not the threshold value.

## Tests

### `tests/core/test_simplify.py` (modify)

Add tests inside class `TestCollectIssueDiffStats`. Each test uses the existing helpers `_init_git_repo`, `_write_issue_file`, `_commit_file`, `_commit_content` already defined in the file.

- **test_excludes_claude_paths**: stages a commit to `claude/commands/mantle/foo.md` under `feat(issue-7):` conventional commit; asserts `stats == DiffStats(0, 0, 0, 0)`. Demonstrates that out-of-scope paths alone don't count.
- **test_excludes_mantle_paths**: stages a commit to `.mantle/learnings/x.md` under `feat(issue-7):`; asserts `stats == DiffStats(0, 0, 0, 0)`. Covers the issue-62 scenario where auto-commits to `.mantle/` inflated the count.
- **test_counts_only_src_and_tests_when_mixed**: stages two commits under `feat(issue-7):` — one adding 10 lines to `src/foo.py`, one adding 20 lines to `claude/bar.md`. Assert `stats.files == 1`, `stats.lines_added == 10`, `stats.lines_changed == 10`. Directly mirrors the issue-62 scenario.
- **test_counts_tests_directory**: stages a commit to `tests/test_foo.py` (5 lines added) under `feat(issue-7):`; asserts `stats.files == 1`, `stats.lines_changed == 5`. Confirms `tests/` is included.

Each test must create the parent directory (e.g. `(project / "src").mkdir()`) before writing the file — the existing helpers write directly under `project_root` and don't handle subdirectories. Use `Path.mkdir(parents=True, exist_ok=True)` or extend a small local helper inline.

Existing tests (`test_single_commit`, `test_multi_commit_aggregation`, etc.) commit files at the project root (e.g. `foo.py`, not `src/foo.py`) — those tests will now report `DiffStats(0, 0, 0, 0)` under the new filter. Update each affected existing test to place files under `src/` (the minimal change: rename `"foo.py"` → `"src/foo.py"`, `"a.py"` → `"src/a.py"`, `"b.py"` → `"src/b.py"`, `"padded.py"` → `"src/padded.py"`), so the existing assertions still hold. This keeps the test suite's coverage of the other branches (padded single-digit, multi-commit, pure deletion, no-commits) intact.

Run `uv run pytest tests/core/test_simplify.py` locally to confirm green before committing.