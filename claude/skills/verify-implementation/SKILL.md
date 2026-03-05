---
name: verify-implementation
description: Post-implementation verification — lint, type-check, test, and review against story spec
allowed-tools: Read, Grep, Glob, Bash
context: fork
agent: general-purpose
user-invocable: false
---

You are verifying that a story was implemented correctly. You receive the story specification and must check the implementation against it.

## Verification Steps

1. **Run tests**: Execute `uv run pytest` and confirm all tests pass.

2. **Run checks**: Execute `just check` to run lint, type-check, and formatting checks. If `just` is not available, run:
   - `uv run ruff check src/ tests/`
   - `uv run mypy src/`

3. **Story compliance**: For each item in the story's ## Implementation section, verify the code exists and matches the specification:
   - Are all specified files created/modified?
   - Do function signatures match?
   - Are design decisions followed?

4. **Test coverage**: For each test case in the story's ## Tests section, verify:
   - The test exists
   - The test name and purpose match the spec

## Output

Report a summary:

- **Tests**: PASS/FAIL (with failure details if any)
- **Checks**: PASS/FAIL (with issues if any)
- **Story compliance**: list of spec items with DONE/MISSING
- **Verdict**: PASS (all good) or FAIL (with what needs fixing)
