---
issue: 83
title: Make collect-issue-diff-stats source/test paths configurable for non-src/tests
  projects
approaches:
- A — Additive categorised API (chosen)
- B — Replace DiffStats signature with dict[str, DiffStats]
chosen_approach: A — Additive categorised API
appetite: small batch
open_questions:
- None
author: 110059232+chonalchendo@users.noreply.github.com
created: '2026-04-21'
updated: '2026-04-21'
updated_by: 110059232+chonalchendo@users.noreply.github.com
tags:
- type/shaped
- phase/shaping
---

# Issue 83 — Make collect-issue-diff-stats source/test paths configurable

## Context

`collect-issue-diff-stats` hardcodes `-- src/ tests/` as its git diff pathspec (`src/mantle/core/simplify.py:200-201`). Fine for this repo; broken for dbt-style projects (`models/`, `tests/`, `macros/`), JS monorepos (`app/`, `__tests__/`), and anything else that doesn't use the `src/tests` layout. This blocks Mantle adoption on the user's real work repos.

The only existing consumer is `claude/commands/mantle/build.md` Step 7's simplify-skip condition, which reads `files` and `lines_changed` from the key=value output. That contract must stay stable (issue slice excludes `claude-code`).

## Skills read

- `pydantic-project-conventions` → `.claude/skills/pydantic-project-conventions/references/core.md` — confirmed plain `type | None = None` field pattern used by `_ConfigFrontmatter`. No MentatModel base applies here (this is internal config, not connector data).
- `cli-design-best-practices` → `.claude/skills/cli-design-best-practices/references/core.md` — structured-output versioning rule: new output lines must be additive; never redefine existing keys (`files=`, `lines_changed=`).

## Approaches evaluated

### A — Additive categorised API (chosen, small batch)

Keep the existing `collect_issue_diff_stats(...) -> DiffStats` function returning today's source+test aggregate. Add a new `collect_issue_diff_stats_categorised(...) -> dict[str, DiffStats]` function that returns per-category stats plus an `\"other\"` bucket when configuration is explicit. CLI prints both the legacy aggregate lines and new per-category lines.

- **Pros:** fully additive. Existing ~10 unit tests, existing CLI consumers (build.md Step 7), and existing output format are unchanged. No claude-code slice widening needed.
- **Cons:** two public functions in `core/simplify.py` doing overlapping work. The aggregate one is a thin wrapper. Acceptable duplication for stability.

### B — Replace signature

Change `collect_issue_diff_stats(...) -> dict[str, DiffStats]` and update CLI + build.md Step 7 to compute aggregate from the dict.

- **Pros:** one function.
- **Cons:** widens slice into `claude-code` (build.md edit), breaks ~10 existing tests, breaks any external callers that rely on the `DiffStats` return. Not small batch.

### Decision

Approach A — minimum change for AC satisfaction, cleanest slice boundary, preserves the CLI output contract.

## Code design for chosen approach

### Strategy

- **`src/mantle/core/project.py::_ConfigFrontmatter`** — add field `diff_paths: dict[str, list[str]] | None = None`. Stored in `.mantle/config.md` frontmatter.
- **`src/mantle/core/simplify.py`** — new module-level constants and functions:
  - `DEFAULT_DIFF_PATHS: dict[str, tuple[str, ...]] = {\"source\": (\"src/\",), \"test\": (\"tests/\",)}`
  - `PRIMARY_CATEGORIES: frozenset[str] = frozenset({\"source\", \"test\"})` — the two keys whose DiffStats sum to the legacy `files`/`lines_changed` aggregate used by build.md's simplify-skip condition.
  - `load_diff_paths(project_root: Path) -> tuple[dict[str, tuple[str, ...]], bool]` — reads `.mantle/config.md`, returns `(mapping, is_custom)`. `is_custom` is `True` when the `diff_paths` field is present (enables the \"other\" bucket).
  - `collect_issue_diff_stats_categorised(project_root: Path, issue: int) -> dict[str, DiffStats]` — runs one `git diff --numstat <first>^..<last>` (file-level, no `--` filter), groups each file by category (first matching prefix wins), computes per-category DiffStats. Adds `\"other\"` key when `is_custom` and unclassified files exist. Categories always present (zero stats if empty).
  - `collect_issue_diff_stats(project_root: Path, issue: int) -> DiffStats` — kept as today's aggregate. Now implemented as a thin wrapper: call the categorised variant, sum DiffStats for keys in `PRIMARY_CATEGORIES`. Signature and semantics unchanged.
- **`src/mantle/cli/simplify.py::run_collect_issue_diff_stats`** — call categorised variant once; emit legacy aggregate lines (`files=N`, `lines_added=N`, `lines_removed=N`, `lines_changed=N`) computed from the primary categories, then per-category lines (`<category>_files=N`, `<category>_lines_added=N`, `<category>_lines_removed=N`, `<category>_lines_changed=N`) in insertion order.
- **Tests:**
  - `tests/core/test_simplify.py` — new `TestCollectIssueDiffStatsCategorised` class covering: defaults match today's behaviour (no \"other\" key), explicit config produces \"other\" bucket, dbt-style fixture (`models/`, `tests/`, `macros/`) reports sensible stats. Existing `TestCollectIssueDiffStats` tests untouched.
  - `tests/cli/test_simplify.py` — new CLI test asserting per-category lines appear alongside aggregate lines.

### Fits architecture by

- Config field joins existing `_ConfigFrontmatter` (plain Pydantic `type | None = None` pattern per pydantic-project-conventions skill).
- New domain function lives alongside existing `collect_issue_diff_stats` in `core/simplify.py`; core stays pure (no CLI imports — honours `core/ never imports cli/` invariant from CLAUDE.md).
- CLI output is purely additive per cli-design-best-practices rule 3: new lines, same keys; build.md Step 7's grep for `files=`/`lines_changed=` keeps working.
- No new migration — missing `diff_paths` frontmatter falls back to `DEFAULT_DIFF_PATHS`.

### Does not

- Does not change `DiffStats` NamedTuple shape (existing callers unaffected).
- Does not edit `claude/commands/mantle/build.md` — aggregate keys are stable by design; slice stays `core, cli, tests`.
- Does not add `--json` output flag (out of scope for this issue).
- Does not migrate existing `.mantle/config.md` files — absent field = defaults, no user action required.
- Does not validate prefix strings (trailing slash, absolute paths, etc.) — Pydantic type-checks only. Malformed prefixes simply fail to match and files land in \"other\".
- Does not re-categorise the build pipeline's simplifier scope (still pinned to `src/ tests/` in build.md Step 7's git diff command — that's a separate concern).