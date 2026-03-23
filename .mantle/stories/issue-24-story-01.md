---
issue: 24
title: Core simplify module — file collection and diff utilities
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a developer, I want /mantle:simplify to automatically identify which files were changed by an issue's implementation, so that the simplification pass targets only relevant code.

## Approach

Follows the thin-module pattern of core/verify.py. Provides utility functions that the Claude Code command (simplify.md) will call via the mantle CLI. Builds on core/issues.py for issue loading and git for diff collection. This is the foundation story — story 2 will add the Claude Code command that orchestrates everything.

## Implementation

### src/mantle/core/simplify.py (new file)

- `collect_issue_files(project_root: Path, issue: int) -> tuple[str, ...]`
  - Loads the issue via `issues.load_issue()`
  - Runs `git log --oneline --grep="issue-{N}" --format="%H"` to find commits matching the issue's conventional commit pattern `feat(issue-N):`
  - Runs `git diff --name-only {first_commit}^..{last_commit}` to collect changed files
  - Returns tuple of file paths relative to project root
  - Raises `NoCommitsFoundError` if no matching commits exist

- `collect_changed_files(project_root: Path) -> tuple[str, ...]`
  - Runs `git diff --name-only HEAD` for unstaged + staged changes
  - Also includes untracked files from `git ls-files --others --exclude-standard`
  - Returns tuple of file paths relative to project root

- `NoCommitsFoundError(Exception)` — raised when no commits match the issue pattern

- `LLM_BLOAT_CHECKLIST: str` — a constant string containing the 8-item bloat pattern checklist (unnecessary abstractions, defensive over-engineering, code duplication, unnecessary conditionals, dead code, comment noise, slop scaffolding, over-parameterisation). Formatted as markdown for inclusion in agent prompts.

#### Design decisions

- **Git subprocess calls**: Use `subprocess.run` with `capture_output=True, text=True, check=True` — same pattern as `state.resolve_git_identity()`
- **Commit detection via grep**: Relies on conventional commit format `feat(issue-N):` which is enforced by implement.md. Simple and reliable.
- **Bloat checklist as constant**: Hardcoded in core, not configurable. Keeps it simple — configurability is a rabbit hole identified in shaping.

### src/mantle/cli/simplify.py (new file)

- `run_collect_issue_files(*, issue: int, project_dir: Path | None = None) -> None`
  - Calls `simplify.collect_issue_files()`, prints file list
  - Catches `NoCommitsFoundError`, prints user-friendly error, raises `SystemExit(1)`

- `run_collect_changed_files(*, project_dir: Path | None = None) -> None`
  - Calls `simplify.collect_changed_files()`, prints file list

### src/mantle/cli/main.py (modify)

- Register `collect-issue-files` command: `--issue` (int, required), `--path` (optional)
- Register `collect-changed-files` command: `--path` (optional)

## Tests

### tests/core/test_simplify.py (new file)

- **test_collect_issue_files_finds_matching_commits**: Create a tmp git repo with commits following `feat(issue-1):` pattern, verify correct files returned
- **test_collect_issue_files_no_commits_raises**: Empty repo raises `NoCommitsFoundError`
- **test_collect_issue_files_excludes_other_issues**: Commits for issue-2 not included when collecting for issue-1
- **test_collect_changed_files_includes_staged_and_unstaged**: Stage one file, modify another, verify both returned
- **test_collect_changed_files_includes_untracked**: New untracked file included in results
- **test_collect_changed_files_empty_when_clean**: Clean working tree returns empty tuple
- **test_bloat_checklist_contains_all_patterns**: Verify `LLM_BLOAT_CHECKLIST` contains all 8 pattern names

### tests/cli/test_simplify.py (new file)

- **test_run_collect_issue_files_prints_files**: Happy path, verifies output
- **test_run_collect_issue_files_no_commits_exits**: Verifies `SystemExit(1)` on `NoCommitsFoundError`
- **test_run_collect_changed_files_prints_files**: Happy path