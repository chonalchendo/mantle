---
issue: 55
title: Collapse per-story code review into simplify step
approaches:
- Clean cut — remove per-story reviewer; composite skip heuristic via new CLI helper;
  simplify checklist unchanged
- Always simplify — remove reviewer and drop skip condition entirely
chosen_approach: Clean cut
appetite: small batch
open_questions:
- Default threshold for lines_changed — start at 50 and tune based on first few real
  builds
author: 110059232+chonalchendo@users.noreply.github.com
created: '2026-04-12'
updated: '2026-04-12'
updated_by: 110059232+chonalchendo@users.noreply.github.com
tags:
- type/shaped
- phase/shaping
---

## Context

The build pipeline runs two overlapping quality checks — a per-story code-reviewer agent (implement.md step 7) and a post-implementation simplify step (build.md step 7). Five of the eight simplify bloat patterns overlap with what the code reviewer checks. TDD already covers spec compliance. The per-story pass runs N times, most return PASS, and it misses cross-story patterns the simplify pass does catch. See brainstorm `2026-04-11-collapse-code-review-into-simplify.md`.

## Approaches

### A — Clean cut (chosen, small batch)

Remove the per-story code-reviewer step and its fix cycle from `implement.md` step 7. Update `build.md` step 7 skip condition from "≤3 files" to a composite heuristic "≤3 files AND ≤N lines changed". Add a small CLI helper so build.md can read both numbers in one call. Simplify checklist unchanged.

- **Tradeoffs:** Minimal change, single quality gate, fewer tokens per build. Needs a sensible default threshold.
- **Rabbit holes:** Threshold tuning — if too low, trivial builds run simplify; if too high, real builds skip it. Start with files≤3 AND lines≤50 and iterate.
- **No-gos:** Not absorbing any checks into the simplify checklist; not touching /mantle:simplify standalone behaviour; not removing the code-reviewer agent type from the system.
- **Side-effect scan:** build.md step 7 is the only caller of the new stats helper — no CLI ordering dependencies. implement.md change is purely a step removal, no downstream state transitions affected.

### B — Always simplify (rejected)

Same removal, drop the skip condition entirely so simplify always runs in build mode.

- **Rejection reason:** Violates AC 5 (small issue must skip simplification) and AC 6 (large issue must trigger it). AC 5/6 explicitly require a composite threshold, not "always on".

## Chosen approach — Clean cut

Small batch, all 6 ACs satisfied.

## Code design

### Strategy

- **`claude/commands/mantle/implement.md`** — remove step 7 (Post-implementation review) and its fix-cycle paragraph. Renumber subsequent sub-steps (8→7, 9→8). Update step 4's TaskCreate list if it references step 7.
- **`claude/commands/mantle/build.md`** step 7 — replace `mantle collect-issue-files --issue {NN}` file-count check with a call to `mantle collect-issue-diff-stats --issue {NN}` returning files+lines. Skip only if **files ≤ 3 AND lines_changed ≤ 50**. Report skip/run message as before.
- **`src/mantle/core/simplify.py`** — add `collect_issue_diff_stats(project_root, issue) -> DiffStats` where `DiffStats` is a `typing.NamedTuple` with fields `files: int`, `lines_added: int`, `lines_removed: int`, `lines_changed: int` (added+removed). Reuse existing commit-discovery via `_grep_commits`; call `git diff --shortstat <first>^..<last>` and parse the single-line summary. Raise `FileNotFoundError` for unknown issues, match existing style.
- **`src/mantle/cli/simplify.py`** — add `run_collect_issue_diff_stats(*, issue, project_dir=None)` printing each field on its own line (`files=N`, `lines_added=N`, `lines_removed=N`, `lines_changed=N`) for easy Bash parsing. Also print a human-readable summary line.
- **`src/mantle/cli/main.py`** — register the new subcommand `collect-issue-diff-stats`.
- **Tests** — mirror `tests/core/test_simplify.py` with a `test_collect_issue_diff_stats.py` case covering: no commits → zeros, single commit with known diff, multi-commit aggregation, unknown issue raises. Mock nothing; drive via real git in `tmp_path`.

### Fits architecture by

- Honours the core-never-imports-cli boundary (`CLAUDE.md`): git work in `core/simplify.py`, printing in `cli/simplify.py`.
- Reuses the `_grep_commits` pattern already in `collect_issue_files`, following the convention established by issue 45 (archive scan in `next_issue_number`).
- Keeps `LLM_BLOAT_CHECKLIST` unchanged (AC 3).
- `/mantle:simplify` standalone keeps working — it never calls the skip-condition logic, which lives only in `build.md` (AC 4).
- Follows Google style (`google-python-style`): absolute imports, Google docstrings, type hints, 80-col.

### Does not

- Does not modify the simplify checklist content (AC 3).
- Does not touch `/mantle:simplify` standalone command behaviour (AC 4).
- Does not remove the `code-reviewer` agent type from the system — only stops implement.md from spawning it.
- Does not add any per-wave or mid-pipeline review.
- Does not change implement.md's learnings extraction (current step 9).
- Does not change state-transition CLIs or issue/story schemas.