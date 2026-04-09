---
issue: 29
title: Core introspection and structured strategy generation
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a developer, I want my verification strategy to be auto-detected from my project setup so I don't have to describe it from scratch.

## Depends On

None — independent.

## Approach

Add two functions to core/verify.py: introspect_project() reads project files to detect test/lint/check commands, and generate_structured_strategy() renders the detections into a structured markdown strategy string. Follows the existing pattern of core functions with simple interfaces hiding file-reading complexity.

## Implementation

### src/mantle/core/verify.py (modify)

Add two new public functions after the existing save_strategy function:

**introspect_project(project_root: Path) -> dict[str, str | None]**:
- Read CLAUDE.md at project_root — look for lines containing 'pytest', 'just check', 'just fix', 'uv run', test/lint commands
- Read pyproject.toml at project_root — check [project.scripts], [tool.pytest], [tool.ruff] sections
- Read Justfile at project_root — look for recipes named 'test', 'check', 'lint', 'fix'
- Read Makefile at project_root — look for targets named 'test', 'check', 'lint'
- Return dict with keys: test_command, lint_command, check_command, type_check_command (values are detected command strings or None)
- Use simple string matching — no TOML parser dependency. Read file as text and search for patterns.

**generate_structured_strategy(introspection: dict[str, str | None]) -> str**:
- Takes the dict from introspect_project
- Returns a multiline string with markdown sections:
  ```
  ## Test Command
  {test_command or 'Not detected — configure manually'}

  ## Lint/Format Check
  {lint_command or 'Not detected'}

  ## Type Check
  {type_check_command or 'Not detected'}

  ## Acceptance Criteria Verification
  Run the test suite, then verify each acceptance criterion independently by reading implementation code, checking file existence, and confirming behaviour matches the specification.
  ```
- If check_command is detected and covers multiple concerns (e.g. 'just check' runs lint+type+test), note it in the relevant sections

#### Design decisions

- **No TOML parser**: Read pyproject.toml as plain text to avoid adding a dependency. Pattern matching on key names is sufficient for detection.
- **Best-effort detection**: Return None for anything not confidently detected. The prompt handles missing values gracefully.
- **Dict not dataclass**: Simple dict return type keeps the interface thin and avoids a new model for 4 optional strings.

## Tests

### tests/core/test_verify.py (modify)

Add a new test class TestIntrospectProject:

- **test_detects_pytest_from_claude_md**: Create a CLAUDE.md with 'Run tests: uv run pytest', verify test_command is 'uv run pytest'
- **test_detects_just_check_from_claude_md**: Create a CLAUDE.md with 'Run all checks: just check', verify check_command is 'just check'
- **test_detects_from_justfile**: Create a Justfile with a 'test' recipe containing 'uv run pytest', verify test_command detected
- **test_detects_ruff_from_pyproject**: Create pyproject.toml with [tool.ruff] section, verify lint_command detected
- **test_no_files_returns_none_values**: Empty project dir, all values are None
- **test_claude_md_takes_priority**: When both CLAUDE.md and Justfile have test commands, CLAUDE.md wins (it's the user's explicit config)

Add a new test class TestGenerateStructuredStrategy:

- **test_all_detected**: Pass dict with all values set, verify output has all sections populated
- **test_none_values_show_not_detected**: Pass dict with all None, verify 'Not detected' appears in output
- **test_partial_detection**: Pass dict with only test_command set, verify structure is correct