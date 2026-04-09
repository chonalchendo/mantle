---
issue: 45
title: Fix issue numbering to include archive — prevent reused numbers
approaches:
- A — Inline archive scan in next_issue_number
- B — New _all_known_issue_numbers helper
- C — Add include_archive param to list_issues
chosen_approach: A — Inline archive scan in next_issue_number
appetite: small batch
open_questions: []
author: 110059232+chonalchendo@users.noreply.github.com
created: '2026-04-09'
updated: '2026-04-09'
updated_by: 110059232+chonalchendo@users.noreply.github.com
tags:
- type/shaped
- phase/shaping
---

## Chosen approach: A — Inline archive scan in next_issue_number

Build-mode auto-selected the smallest-appetite approach that satisfies all ACs. All three candidates were small-batch; A wins because it has zero blast radius and requires no public API changes.

### Approaches considered

| | A: Inline archive scan | B: New helper `_all_known_issue_numbers` | C: `list_issues(include_archive=True)` |
|---|---|---|---|
| Appetite | small batch | small batch | small batch |
| Key benefit | Minimal, no API change | Reusable for future archive-aware code | Explicit in public API |
| Key risk | Slight glob duplication | Speculative (one caller only) | `list_issues` also feeds `count_issues` which must stay active-only |

C was rejected because `list_issues` has two callers: `next_issue_number` (wants archive-inclusive) and `count_issues` (must stay active-only — it's the "active issues in backlog" counter for status display). Changing `list_issues` semantics would corrupt `count_issues`.

B was rejected as speculative. There is exactly one caller that needs archive-inclusive numbering (`next_issue_number`). Adding a helper for one caller is YAGNI.

A keeps the change local to the one function that has the bug.

## Strategy

- Modify `next_issue_number` in `src/mantle/core/issues.py` (currently lines 172-190).
- Add a second glob pass on `.mantle/archive/issues/issue-*.md`, using the same `re.compile(r"issue-(\d+)-.*\.md")` pattern.
- Fold both scans into the same `highest = max(highest, ...)` loop.
- `list_issues`, `count_issues`, `find_issue_path` are untouched.

Key code locations:
- `src/mantle/core/issues.py:172` — `next_issue_number` function
- `tests/core/test_issues.py` — add 3 new test cases

## Fits architecture by

- Stays entirely in `core/issues.py` — honours the `core/` import boundary per CLAUDE.md (`core/` never imports from `cli/` or `api/`).
- Uses the existing `project.resolve_mantle_dir()` helper for path resolution — consistent with how `list_issues` already does it at line 166.
- No CLI command changes. No prompt changes. No frontmatter changes.
- Follows Google Python Style Guide: type hints preserved, Google-style docstring updated to mention archive.
- Follows `software-design-principles` (Ousterhout): deep module — don't widen the interface, add internal logic.

## Does not

- Does not modify `list_issues` (would break `count_issues`'s "active count" semantics used for status displays).
- Does not add archive scanning to `find_issue_path` or `issue_exists` (separate concern — not in acceptance criteria).
- Does not fix the pre-existing regex quirk that ignores numeric-only `issue-NN.md` format files (also out of scope — the bug report is about slug-format collisions, which is what the regex does match).
- Does not change any CLI command, prompt, or configuration file.
- Does not archive/unarchive anything — only the numbering lookup changes.