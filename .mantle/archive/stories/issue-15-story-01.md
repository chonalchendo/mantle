---
issue: 15
title: Core verify module — strategy loading, report building, status transition
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a developer, I want verification logic that loads my project's strategy (with per-issue overrides) and produces a structured pass/fail report, so that `/mantle:verify` has reliable core functions to call.

## Approach

Follows the same pattern as `core/shaping.py` and `core/learning.py` — Pydantic models for data, public functions for CRUD, `core/project.py` for config access. Builds on existing `read_config()`/`update_config()` in `project.py` and the `verification` field already on `IssueNote`. This is the foundation story; story 2 adds the user-facing command and CLI wiring.

## Implementation

### src/mantle/core/verify.py (new file)

- **`VerificationResult`** — frozen Pydantic BaseModel: `criterion: str`, `passed: bool`, `detail: str | None = None`
- **`VerificationReport`** — frozen Pydantic BaseModel: `issue: int`, `title: str`, `results: tuple[VerificationResult, ...]`, `strategy_used: str`, `is_override: bool` (whether per-issue override was used). Property `passed` returns `all(r.passed for r in self.results)`.
- **`load_strategy(project_root: Path, issue_number: int) -> tuple[str, bool]`** — loads verification strategy. Reads issue file via `issues.load_issue()` to check for per-issue `verification` override. If override exists, returns `(override, True)`. Otherwise reads config via `project.read_config()` and returns `(strategy, False)`. Raises `VerificationStrategyNotFoundError` if neither exists.
- **`save_strategy(project_root: Path, strategy: str) -> None`** — persists strategy to config.md via `project.update_config(project_root, verification_strategy=strategy)`.
- **`build_report(issue_number: int, title: str, results: list[tuple[str, bool, str | None]], strategy_used: str, is_override: bool) -> VerificationReport`** — constructs a `VerificationReport` from raw results tuples.
- **`format_report(report: VerificationReport) -> str`** — renders report as markdown string with checkmarks/crosses per criterion.
- **`VerificationStrategyNotFoundError(Exception)`** — raised when no strategy found in config or issue.

#### Design decisions

- **No execution logic in core**: The core module loads strategy and builds reports, but does not *execute* verification steps. Execution is done by the AI agent in the verify.md command (it reads the strategy, runs the steps, and reports results). This keeps core pure and testable.
- **Reuse existing config functions**: `project.read_config()` and `project.update_config()` already handle config.md — no need to duplicate.
- **Tuple for results**: Frozen Pydantic models with tuples, matching the project convention (see `ShapedIssueNote`, `LearningNote`).

### src/mantle/core/issues.py (modify)

- Add a **`transition_to_verified(project_root: Path, issue_number: int) -> Path`** function that loads the issue, validates current status allows transition (must be `implementing` or `implemented`), updates status to `verified`, updates tags, writes back. Returns the path. Raises `InvalidTransitionError` if status doesn't allow it.

## Tests

### tests/core/test_verify.py (new file)

- **test_load_strategy_from_config**: Set up config.md with `verification_strategy`, call `load_strategy()`, assert returns `(strategy, False)`
- **test_load_strategy_per_issue_override**: Set up issue with `verification` field, call `load_strategy()`, assert returns `(override, True)` and override takes precedence
- **test_load_strategy_not_found**: No strategy in config, no override on issue, assert raises `VerificationStrategyNotFoundError`
- **test_save_strategy**: Call `save_strategy()`, read config back, assert `verification_strategy` is persisted
- **test_build_report_all_pass**: Build report with all passing results, assert `report.passed` is `True`
- **test_build_report_some_fail**: Build report with mixed results, assert `report.passed` is `False`
- **test_format_report**: Build and format report, assert markdown contains checkmarks for passed and crosses for failed
- **test_transition_to_verified**: Issue with status `implemented`, call `transition_to_verified()`, assert status updated to `verified`
- **test_transition_to_verified_invalid_status**: Issue with status `planned`, assert raises `InvalidTransitionError`

Fixtures: `tmp_path` with `.mantle/` directory structure, `config.md` with frontmatter, issue files in `issues/`.