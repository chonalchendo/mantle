---
issue: 63
title: Align simplify skip-threshold stats with simplify scope
approaches:
- 'A: Default-filter collect-issue-diff-stats to src/+tests/'
- 'B: Add --scope flag, default unchanged'
- 'C: Inline the git diff in build.md Step 7'
chosen_approach: 'A: Default-filter collect-issue-diff-stats to src/+tests/'
appetite: small batch
open_questions:
- Future reporting callers that want full-repo line counts will need a flag; add only
  when that caller appears.
author: 110059232+chonalchendo@users.noreply.github.com
created: '2026-04-17'
updated: '2026-04-17'
updated_by: 110059232+chonalchendo@users.noreply.github.com
tags:
- type/shaped
- phase/shaping
---

## Shaping Context

Issue 62's retrospective (2026-04-17) surfaced a misalignment: `/mantle:build` Step 7 gates simplification on `mantle collect-issue-diff-stats --issue {NN}`, which currently counts *all* changed lines in the repo. The simplifier itself is scoped to `src/` + `tests/` via `git diff --name-only $PRE_IMPLEMENT_REV..HEAD -- src/ tests/`. For issue 62: full count was `files=2, lines_changed=55` (above the 50 threshold → simplify ran), but the in-scope diff was 17 lines of test code. The simplifier was invoked with nothing meaningful to simplify.

## Grep evidence

`rg collect-issue-diff-stats` across the repo finds:
- `src/mantle/cli/main.py` — defines the command
- `src/mantle/core/simplify.py` — implements the function
- `claude/commands/mantle/build.md` — **the only external caller** (Step 7)
- `tests/core/test_simplify.py`, `tests/cli/test_simplify.py` — unit tests of the function/CLI
- `.mantle/learnings/issue-62-...` — the retro notes that surfaced this issue

There is no other `/mantle:*` prompt, no script, no `mantle` subcommand that consumes the stats. Only Step 7 cares. This directly answers the question posed in the issue body ("Prefer (b) if other callers want the full count; prefer (a) if Step 7 is the only caller today.").

## Approaches

### A: Default-filter `collect-issue-diff-stats` to `src/` + `tests/`  [CHOSEN]

- Change `core/simplify.py::collect_issue_diff_stats` so its `git diff --stat` and `--numstat` calls use pathspec `-- src/ tests/`.
- CLI signature unchanged. No new flag.
- Build.md Step 7 is unchanged prose-wise, except that the scope-filter bash line no longer needs to exist as a separate definition — the gate stat and the agent's edit list now both live on the same paths.
- Appetite: small batch (single-function core edit + 1 prompt edit + 1 unit test).
- Tradeoff: if a future caller wants full-repo stats, they need to opt out. No such caller exists today. Cost of adding a `--scope all` flag later if needed: trivial.

### B: Add `--scope {all,src-tests}` flag, default `all`

- Preserves backward compat (no default change).
- Build.md Step 7 adds `--scope src-tests` to its invocation.
- YAGNI: the `all` variant has no consumer. Designing the flag before a user exists violates `cli-design-best-practices` (structured output format changes without versioning / flag surface reserved for concrete needs).

### C: Inline the git diff in build.md Step 7

- Drop the CLI call entirely; compute the stats directly in a bash snippet inside the prompt.
- Structurally impossible to drift since the same `git diff` with the same pathspec is used once.
- But pushes business logic (line-counting + threshold check) into the prompt template, making it harder to unit-test and harder for humans to reason about.
- Rejected: violates `design-review` rule against implementation-in-docs (red flag #10).

## Rationale for A

- Grep shows Step 7 is the only caller. YAGNI rules out B's flag.
- A keeps the business logic in `core/simplify.py` where it's testable.
- A leaves the Step 7 prose simpler: one scope, one stat, one source of truth. The reader does not have to cross-reference two definitions of "changed lines".
- A satisfies AC3 by construction: for issue 62's commit range, `src/`+`tests/` has 17 lines changed, below 50 → gate would now skip simplify correctly.

## Code design

### Strategy

Modify `src/mantle/core/simplify.py::collect_issue_diff_stats(project: Path, issue_number: int) -> DiffStats` to pass `pathspec=["src/", "tests/"]` (or positional `-- src/ tests/`) to the underlying `git diff --stat` / `--numstat` calls. The `DiffStats` dataclass/return type is unchanged. The CLI command `src/mantle/cli/main.py::collect_issue_diff_stats_command` is unchanged — it forwards to the core function which now does the filtering.

Update `claude/commands/mantle/build.md` Step 7:
- Skip-condition prose and thresholds (`files ≤ 3`, `lines_changed ≤ 50`) unchanged.
- Remove the separate `git diff --name-only $PRE_IMPLEMENT_REV..HEAD -- src/ tests/` line OR add a note that the pathspec is identical to what the stats command counts, so the two cannot drift. Prefer the former — one fewer line of prose.

Add a unit test in `tests/core/test_simplify.py` (follows the existing fixture pattern that sets up a git repo in `tmp_path` and stages committed changes). The test stages changes across three paths: `src/foo.py` (in-scope), `tests/test_foo.py` (in-scope), and `claude/commands/foo.md` (out-of-scope). Assert the returned `DiffStats` only counts the first two.

### Fits architecture by

- Core-only change: `core/` stays pure, `cli/` forwards, no new surface.
- Respects the `core-never-imports-cli` boundary from CLAUDE.md.
- Tests file mirrors source file per project convention (`tests/core/test_simplify.py` ↔ `src/mantle/core/simplify.py`).
- Removes implementation-in-docs (red flag #10 from design-review): build.md no longer needs to define "what counts as a line changed".

### Does not

- Does not add a `--scope` flag (no current caller needs one).
- Does not change the 3-file / 50-line thresholds (out of scope per AC list).
- Does not refactor the simplifier agent's own diff computation (already scoped correctly).
- Does not touch `.mantle/` churn handling or auto-commit hooks.
- Does not change the `DiffStats` return type or CLI output format.
- Does not migrate existing callers (there are no other callers).

## Open questions

- If/when a reporting/telemetry caller wants full-repo stats, add `--scope {src-tests,all}` then. Single flip, no migration cost.