---
issue: 80
title: Fix cyclopts --pass/--fail binding and add CLI-path test
status: in-progress
failure_log: null
tags:
- type/story
- status/in-progress
---

## User Story

As an agent running /mantle:verify, I want the documented `mantle flip-ac --issue N --ac-id X --pass` command to execute without error on the first try, so that I can record verification results without falling into a broken code path.

## Depends On

None — independent.

## Approach

Single-file production fix in `src/mantle/cli/main.py` using cyclopts's first-class `negative=` parameter to bind `--pass`/`--fail` as a true boolean pair — the slash-in-name syntax currently used is not a cyclopts convention and only produces a working `--fail`. Test coverage for the CLI path (invoking `main.app(...)` in-process) is the missing half — existing tests call `run_flip_ac(...)` directly and therefore do not exercise the cyclopts binding.

## Implementation

### src/mantle/cli/main.py (modify)

At `flip_ac_command` around line 965-971, replace the `passes` `Parameter` binding:

Before:
```python
passes: Annotated[
    bool,
    Parameter(
        name="--pass/--fail",
        help="Mark the criterion as passing or failing.",
    ),
] = True,
```

After:
```python
passes: Annotated[
    bool,
    Parameter(
        name="--pass",
        negative="--fail",
        help="Mark the criterion as passing or failing.",
    ),
] = True,
```

No other changes in `main.py`. No changes to `cli/issues.py`, `run_flip_ac`, or any core module.

#### Design decisions

- **Use cyclopts's `negative=` kwarg**: `Parameter` exposes `negative` explicitly for boolean-pair negation. Documented in the `cyclopts` vault skill. The prior `name="--pass/--fail"` was a misread of cyclopts conventions — cyclopts treats the slash literally and auto-generates `--no-pass` instead of binding `--pass`.
- **Keep default `= True`**: Preserves the `--waive` semantics (`passes and not waive`) in `run_flip_ac` (`cli/issues.py:145`).
- **No verify.md changes**: The prose already uses `--pass`; the fix aligns the CLI with the prose, not the other way around.

## Tests

### tests/cli/test_issues.py (modify)

Add a new test class `TestFlipAcCli` after `TestRunFlipAc`. Tests invoke the cyclopts app directly — this exercises the binding that `run_flip_ac()`-level tests bypass.

Import pattern: `from mantle.cli import main as main_module`.

Invocation pattern: `main_module.app(f"flip-ac --issue 1 --ac-id ac-01 --pass --path {project}")`.

- **test_flip_ac_cli_pass_flag_marks_passing**: writes an issue with one unchecked AC via `_write_issue_with_acs`; invokes `main_module.app("flip-ac --issue 1 --ac-id ac-01 --pass --path <project>")`; reloads the issue and asserts `acceptance_criteria[0].passes is True`. Covers ac-01 and ac-03.
- **test_flip_ac_cli_fail_flag_marks_failing**: writes an issue with one already-passing AC; invokes `main_module.app("flip-ac --issue 1 --ac-id ac-01 --fail --path <project>")`; reloads and asserts `.passes is False`. Covers ac-02.

Test fixture requirements: reuses the existing `project` fixture and `_write_issue_with_acs` helper from the same file. No new fixtures. No mocking — actual file I/O against `tmp_path`.

### tests/cli/test_help_groups.py (no change required unless snapshot triggers)

If the help-group inline_snapshot includes the flip-ac `--pass/--fail` line and it changes, refresh via `uv run pytest --inline-snapshot=create` and review the diff before committing.
