---
issue: 29
title: CLI introspect-project command
status: in-progress
failure_log: null
tags:
- type/story
- status/in-progress
---

## User Story

As a developer, I want a CLI command that detects my project's test and lint setup so the verify prompt can propose an informed strategy.

## Depends On

Story 1 — uses core introspect_project and generate_structured_strategy functions.

## Approach

Add a thin CLI wrapper run_introspect_project in cli/verify.py and register it as 'introspect-project' in cli/main.py. Follows the existing pattern of cli/verify.py wrapping core/verify.py functions. Output is JSON for machine consumption by prompts.

## Implementation

### src/mantle/cli/verify.py (modify)

Add new function:

**run_introspect_project(*, project_dir: Path | None = None) -> None**:
- If project_dir is None, default to Path.cwd()
- Call verify.introspect_project(project_dir) to get the dict
- Call verify.generate_structured_strategy(introspection) to get the formatted strategy
- Print the introspection dict as JSON to stdout (for machine consumption)
- Print the generated strategy to stderr with a header (for human readability)
- Import json at module level

### src/mantle/cli/main.py (modify)

Register new command after save-verification-strategy:

```python
@app.command(name="introspect-project")
def introspect_project_command(
    path: Annotated[
        Path | None,
        Parameter("--path", help="Project directory (default: cwd)"),
    ] = None,
) -> None:
    """Detect test, lint, and check commands from project files."""
    verify.run_introspect_project(project_dir=path)
```

#### Design decisions

- **JSON to stdout**: Prompts can parse the output. Human-readable strategy goes to stderr so prompts can capture just the JSON.
- **Thin wrapper**: All logic in core, CLI just routes and prints.

## Tests

### tests/cli/test_verify.py (modify)

Add new test class TestIntrospectProjectCLI:

- **test_outputs_json**: Create project with CLAUDE.md containing test command, run CLI, verify stdout is valid JSON with test_command key
- **test_empty_project**: Run on empty project dir, verify stdout is JSON with null values
- **test_outputs_strategy_to_stderr**: Create project with CLAUDE.md, run CLI, verify stderr contains 'Test Command' section header