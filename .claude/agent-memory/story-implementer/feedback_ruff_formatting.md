---
name: Run just fix before declaring story done
description: Project uses ruff format with 80-col limit; new test files often need reflow
type: feedback
---

After writing or modifying files, always run `just check` (or at minimum `uv run ruff format src/ tests/ --check`) before declaring a story done. Ruff enforces a specific line-wrap style and test files with multi-line path assemblies frequently fail format-check on first write. Use `just fix` to auto-reformat.

**Why:** `just check` runs in CI/pre-commit; leaving unformatted files means the next commit hook or CI run will fail. Caught on issue 46 story 1 where test assembly of archive paths was reformatted by ruff.

**How to apply:** Part of the standard post-implementation sequence — after tests pass, run `just check` before reporting DONE. If format fails, `just fix` and re-run the full suite.
