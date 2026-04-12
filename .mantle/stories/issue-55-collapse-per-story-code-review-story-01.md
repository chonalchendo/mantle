---
issue: 55
title: Core + CLI — collect_issue_diff_stats helper
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a developer, I want a CLI that reports file count and lines changed for an issue so that the build pipeline can decide whether simplification is worth running.

## Depends On

None — independent.

## Approach

Follows the exact pattern of `core/simplify.py::collect_issue_files` — reuse commit discovery via `git log --grep`, then call `git diff --shortstat` across the commit range and parse the single summary line. The CLI wrapper mirrors `run_collect_issue_files` in `cli/simplify.py`. Printed output uses machine-parseable `key=value` lines so `build.md` Bash can read them.

## Implementation

### src/mantle/core/simplify.py (modify)

Add a `DiffStats` NamedTuple and a new public function:

```python
class DiffStats(typing.NamedTuple):
    files: int
    lines_added: int
    lines_removed: int
    lines_changed: int  # added + removed


def collect_issue_diff_stats(
    project_root: Path, issue: int,
) -> DiffStats:
    """Aggregate diff stats across commits for an issue.

    Uses the same commit-discovery logic as collect_issue_files
    (grep for `(issue-N)` and, for N < 10, `(issue-0N)`), then
    runs `git diff --shortstat <first>^..<last>` and parses the
    single summary line (e.g. `5 files changed, 120 insertions(+), 8 deletions(-)`).

    Returns DiffStats(0, 0, 0, 0) when no matching commits exist.
    Raises FileNotFoundError if the issue file does not exist.
    """
```

Implementation notes:
- Reuse the inner `_grep_commits` helper pattern from `collect_issue_files` (extract it to module scope or duplicate inline — duplicate inline to keep the change minimal).
- Call `git diff --shortstat <first>^..<last>` using the same `subprocess.run(..., check=True, cwd=project_root)` pattern.
- Parse the shortstat output with a simple regex: `(\d+) files? changed(?:, (\d+) insertions?\(\+\))?(?:, (\d+) deletions?\(-\))?`. Missing groups default to 0.
- Return zeros if there are no matching commits (same early-return pattern as `collect_issue_files`).
- Do NOT refactor `collect_issue_files` — leave it alone.

### src/mantle/cli/simplify.py (modify)

Add `run_collect_issue_diff_stats`:

```python
def run_collect_issue_diff_stats(
    *, issue: int, project_dir: Path | None = None,
) -> None:
    """Print diff stats for an issue as key=value lines."""
    if project_dir is None:
        project_dir = Path.cwd()
    stats = simplify.collect_issue_diff_stats(project_dir, issue)
    console.print(f"files={stats.files}")
    console.print(f"lines_added={stats.lines_added}")
    console.print(f"lines_removed={stats.lines_removed}")
    console.print(f"lines_changed={stats.lines_changed}")
```

Use plain `console.print` (not rich markup) so Bash parsing is trivial.

### src/mantle/cli/main.py (modify)

Register `collect-issue-diff-stats` subcommand immediately after `collect-issue-files` (around line 1739), mirroring its signature exactly: `--issue` (required int) and `--path` (optional Path, default cwd). Dispatch to `simplify.run_collect_issue_diff_stats`. Docstring: `"Report diff stats (file count, lines added/removed/changed) for an issue's commits."`

#### Design decisions

- **NamedTuple over dataclass**: matches the project's lightweight-value-object convention and gives free equality/tuple access for tests.
- **`lines_changed = added + removed`**: keeps the build.md threshold a single number instead of forcing the prompt to do arithmetic.
- **key=value output**: build.md can grep/cut one line without parsing JSON.
- **No refactor of `collect_issue_files`**: issue explicitly scopes this as additive.

## Tests

### tests/core/test_simplify.py (modify)

Add tests alongside existing `collect_issue_files` tests. Use the same `tmp_path` + real-git fixture pattern (initialise a repo, make commits with conventional-commit subjects, call the function).

- **test_collect_issue_diff_stats_returns_zeros_when_no_commits**: Empty repo with no matching commits → `DiffStats(0, 0, 0, 0)`.
- **test_collect_issue_diff_stats_single_commit**: Make one `feat(issue-7): ...` commit adding a 10-line file → `files=1, lines_added=10, lines_removed=0, lines_changed=10`.
- **test_collect_issue_diff_stats_multi_commit_aggregation**: Two `feat(issue-7): ...` commits touching overlapping and distinct files → aggregate counts across the full range.
- **test_collect_issue_diff_stats_only_deletions**: Commit that only deletes lines → `lines_added=0, lines_removed=N, lines_changed=N`.
- **test_collect_issue_diff_stats_unknown_issue_raises**: Call with an issue number that has no file → `FileNotFoundError`.
- **test_collect_issue_diff_stats_handles_padded_single_digit**: For issue N<10, finds commits written as `feat(issue-0N):` (match existing `collect_issue_files` behaviour).

### tests/cli/test_simplify.py (modify or create)

If the file exists, add; otherwise create mirroring any existing CLI test style.

- **test_run_collect_issue_diff_stats_prints_key_value_lines**: Monkeypatch `core.simplify.collect_issue_diff_stats` to return `DiffStats(3, 42, 5, 47)` and capture stdout (via `capsys`). Assert each of the four `key=value` lines appears.

## Out of scope

- Refactoring `collect_issue_files`.
- Changing build.md or implement.md (separate stories).
- Exposing raw commit range or per-commit stats.