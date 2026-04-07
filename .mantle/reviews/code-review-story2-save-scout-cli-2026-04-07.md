# Code Review: Story 2 — CLI Scout Wiring (save-scout)

**Date:** 2026-04-07
**Files Changed:** 3
**Story:** CLI scout wiring — save-scout subcommand

## Summary
- Critical: 0 | Warnings: 1 | Minor: 2

---

## Part 1 — Spec Compliance

**Verdict: Pass.**

| Requirement | Status | Notes |
|---|---|---|
| Creates `cli/scout.py` with `run_save_scout` | Pass | Present and correctly named |
| Follows `cli/brainstorm.py` pattern | Pass | Structure, signature style, error handling, and output format are consistent |
| Registers `save-scout` command in `main.py` | Pass | `@app.command(name="save-scout")` at line 1313 |
| Import added to `main.py` | Pass | `scout` included in the `from mantle.cli import (...)` block at line 26 |

All four story requirements are delivered.

---

## Part 2 — Code Quality

### Warnings

| Location | Issue | Fix |
|---|---|---|
| `tests/cli/test_scout.py` — `TestRunSaveScout` | No test for the error path. `run_save_scout` raises `SystemExit(1)` on `ValueError`, but there is no test that exercises this branch. The brainstorm test suite includes an equivalent `test_run_save_brainstorm_invalid_verdict` test. This is a meaningful gap: the error branch is untested code. | Add a test that passes invalid input (e.g., an empty `repo_url` if the core layer validates it, or mock `scout.save_scout` to raise `ValueError`) and asserts `SystemExit` with code 1. |

### Minor

| Location | Issue | Fix |
|---|---|---|
| `cli/scout.py` line 51 | The success message says `"Scout report saved to {path.name}"`. The brainstorm equivalent says `"Brainstorm saved to {path.name}"`. Both are fine, but the scout message is slightly more verbose. No action required — this is intentional, not a defect. | No change needed. |
| `tests/cli/test_scout.py` — `TestCLIWiring` | `test_save_scout_help` checks for `"repo-url"` and `"repo-name"` in stdout but does not assert `"dimensions"` or `"content"`. These are required parameters; their absence from the help check is a minor omission. | Add `assert "dimensions" in result.stdout.lower()` and `assert "content" in result.stdout.lower()`. |

### Coding Standards Check

| Standard | Status | Notes |
|---|---|---|
| Type hints on all public functions | Pass | `run_save_scout` is fully annotated |
| Google-style docstrings | Pass | Module docstring present; function has Args and Raises sections |
| 80 character line length | Pass | All lines are within limit |
| Import modules, not individual names | Pass | `from mantle.core import scout` — correct |
| `cli/` depends on `core/`, not reverse | Pass | Dependency direction is correct |
| No bare `except:` | Pass | Catches `ValueError` specifically |
| No mutable default arguments | Pass | |
| `main.py` import style | Pass | Added to the module-level `from mantle.cli import (...)` block |

### Critical Thinking

| Aspect | Observation | Note |
|---|---|---|
| `dimensions` conversion | `run_save_scout` converts `list[str]` to `tuple` before passing to `scout.save_scout`. This is correct if the core layer's type is `tuple[str, ...]`, but it is a silent type coercion at the boundary. If the core signature ever changes, this cast becomes dead code with no warning. | Low risk given the test coverage, but worth noting as a coupling point. |
| `test_run_save_scout_success` and `test_run_save_scout_prints_confirmation` | These two tests exercise the same code path and make overlapping assertions. `test_run_save_scout_success` checks the file is created; `test_run_save_scout_prints_confirmation` checks the output. Merging them or separating concerns more cleanly (one test per observable behaviour) would reduce redundancy without losing coverage. | Minor test-organisation concern, not a correctness issue. |

---

## Recommendations

### Must Fix Before Release
None.

### Should Fix
1. **Add an error-path test** (`test_run_save_scout_value_error`): mock `mantle.core.scout.save_scout` to raise `ValueError("some error")`, call `run_save_scout`, assert `pytest.raises(SystemExit)` with code 1. This brings test coverage in line with the brainstorm pattern the story references.

### Technical Debt (Future)
1. Extend `TestCLIWiring.test_save_scout_help` to assert all four required parameters (`--repo-url`, `--repo-name`, `--dimensions`, `--content`) appear in the help output.

---

## REVIEW: ISSUES

One warning (missing error-path test) and two minor items. No critical defects. The implementation is correct and consistent with the established pattern; the issues are test coverage gaps only.
