# Code Review: Story 2 — list-tags command

**Date:** 2026-04-05
**Files Changed:** 3
**Verdict:** REVIEW: ISSUES

## Summary
- Critical: 0 | Warnings: 2 | Minor: 3

---

## Issues Found

### Warnings

| # | Category | Location | Issue |
|---|----------|----------|-------|
| W1 | quality | `tests/cli/test_main.py:10` | `_ConfigFrontmatter` is imported by name from an internal (underscore-prefixed) symbol, violating the project standard "import modules, not individual names". The correct form is `from mantle.core import project` then `project._ConfigFrontmatter(...)`. |
| W2 | quality | `tests/cli/test_main.py:124, 162` | `mantle = project / ".mantle"` is assigned in both `test_list_tags_flags_undeclared` and `test_list_tags_undeclared_footer` but never used. Dead code. A linter will flag this; it may also cause confusion about intent (was there a planned assertion that was dropped?). |

### Minor

| # | Category | Location | Issue |
|---|----------|----------|-------|
| M1 | spec | `src/mantle/cli/main.py:1050` | Output is `"    - {tag}  (undeclared)"` (two spaces before the parenthesis). The spec says `"(undeclared)" suffix` without specifying spacing, but the double-space is inconsistent with the single-space convention in surrounding output lines. Not a correctness issue, but worth standardising. |
| M2 | quality | `tests/cli/test_main.py:1` | Module docstring says `"Tests for mantle.cli.main — list-tags command."` This file will accumulate tests for more commands over time; the docstring is already misleading. Standard project pattern is `"Tests for mantle.cli.main."` |
| M3 | quality | `tests/cli/test_main.py:102-116` | `test_list_tags_prints_grouped` verifies only that group headers and individual tags appear somewhere in output. It does not verify that the output is actually *grouped* (i.e., that `"Domain:"` precedes `"domain/web"` in the output). The test name claims grouped output is verified, but the assertions only confirm presence. This is a weak behavioural signal; ordering could be asserted with a simple `out.index("Domain:") < out.index("domain/web")` check. |

---

## Spec Compliance Assessment

All four required test cases are present:
- grouped output — covered by `test_list_tags_prints_grouped`
- undeclared flags — covered by `test_list_tags_flags_undeclared`
- no tags — covered by `test_list_tags_no_tags`
- undeclared footer — covered by `test_list_tags_undeclared_footer`

The command follows the `list_skills_command` pattern as specified: lazy import inside the function body, `path` defaulting to `Path.cwd()`, and consistent `@app.command` registration.

`help.md` contains a "Skills & Tags" section with the `mantle list-tags` entry and the workflow tip as specified.

The `tags.collect_all_tags()` call, grouped-by-prefix formatting, `"(undeclared)"` suffix, `"No tags found."` sentinel, and footer with count and `.mantle/tags.md` reference are all present and correct.

---

## Recommendations

### Must Fix Before Release
*(none)*

### Should Fix

1. **W1** — Change `from mantle.core.project import _ConfigFrontmatter` to `from mantle.core import project` and use `project._ConfigFrontmatter(...)` throughout the test file. This brings the test into compliance with the project's import standard.

2. **W2** — Remove the unused `mantle = project / ".mantle"` assignments in `test_list_tags_flags_undeclared` and `test_list_tags_undeclared_footer`. If an assertion against the `.mantle/` path was intended (e.g., confirming `tags.md` is readable after the command), add it; otherwise delete the dead assignment.

### Technical Debt (Future)

1. **M3** — Strengthen `test_list_tags_prints_grouped` to assert ordering, not just presence, if the spec ever formalises that grouped output means tags appear under their section header in the printed output.

2. **M2** — Update the test file module docstring to `"Tests for mantle.cli.main."` to remain accurate as the file grows.
