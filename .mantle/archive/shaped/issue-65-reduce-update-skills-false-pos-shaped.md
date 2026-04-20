---
issue: 65
title: Reduce update-skills false positives from description-overlap matching
approaches:
- 'A: Drop description-overlap rule'
- 'B: Raise token threshold 3 to 5-6'
- 'C: IDF-weight tokens'
chosen_approach: 'A: Drop description-overlap rule'
appetite: small batch
open_questions: []
author: 110059232+chonalchendo@users.noreply.github.com
created: '2026-04-18'
updated: '2026-04-18'
updated_by: 110059232+chonalchendo@users.noreply.github.com
tags:
- type/shaped
- phase/shaping
---

## Why

`core/skills.py:776-778` uses a description-word-overlap rule (3+ non-stopword tokens) that produces false positives in `update-skills --issue NN`. Two inbox reports flagged the defect (issue 45 → DuckLake; issue 48 → Nick Sleep philosophy). Empirical evaluation against issues 40-63 confirms the rule fires mostly on false positives.

## Approaches

### A: Drop description-overlap rule (chosen — small batch)

Remove the rule at `skills.py:775-778` and keep only name/slug/tag matching. Also removes now-dead `_STOPWORDS` frozenset (L24-52), `_tokenize` function (L55-57), and the `content_tokens` precomputation (L749).

**Gain:** zero description-driven false positives; simpler code; easier to reason about matches.
**Give up:** some legitimate skills whose name/slug/tag don't appear literally in the issue body will no longer be auto-matched. Users can add them manually.

### B: Raise threshold 3 → 5-6 (rejected)

Keep the rule, raise the bar. Still probabilistic; verbose issues (e.g., issue 56 with 11 dropped skills) will still over-match. Bandaid.

### C: IDF-weight tokens (rejected — medium batch)

Weight tokens by inverse document frequency over the vault descriptions so common words count less. Correct solution in theory but adds corpus-building, scope creep for a small-batch bug fix.

## Empirical evaluation — per-issue diff (issues 40-63)

Ran current rule vs. rule-dropped against each past issue's body. Total 83 skills would be removed across 24 issues; zero skills added.

| Issue | Dropped (Δ) | Examples (clearly false positives in italics) |
|------|------|------|
| 40 review-feedback | 6 | cyclopts, Design Review, CLI design best practices, *claude-sdk-structured-analysis-pipelines*, *omegaconf* |
| 41 query mantle | 4 | *DuckDB*, *SQLMesh*, *docker-compose-python*, *claude-sdk* |
| 43 global storage | 4 | *Howard Marks*, *Templeton*, *Nick Sleep*, *OpenRouter* |
| 44 hardcoded paths | 9 | *DuckLake*, *Earnings Transcript*, *Finviz*, all 5 investor philosophies |
| 45 numbering | 4 | *DuckDB*, *SQLMesh*, *Templeton*, *docker-compose* |
| 46 save-learning | 3 | *Howard Marks*, *Templeton*, *Nick Sleep* |
| 47 mantleconfig | 2 | *SQLMesh*, *claude-sdk* |
| 48 CLI grouping | 4 | *Designing Architecture*, *FRED*, *Finviz*, *SQLMesh* |
| 49 tag naming | 0 | — |
| 50 staleness tests | 3 | *DuckDB*, *Production Project Readiness*, *claude-sdk* |
| 51 contextual errors | 3 | *DuckLake*, *Production Project Readiness*, *claude-sdk* |
| 52 inject skills | 3 | *Howard Marks*, *Templeton*, *Nick Sleep* |
| 53 skill anatomy | 3 | *Howard Marks*, *Templeton*, *Nick Sleep* |
| 54 build observability | 7 | *Earnings Transcript*, *Nick Sleep*, *edgartools*, *docker-compose*, Software Design Principles |
| 55 per-story review | 7 | *DuckDB*, *SQLMesh*, *Earnings Transcript*, *beautifulsoup4*, *fastapi* |
| 56 lifecycle hooks | 11 | *DuckDB*, *Lakehouse*, *Howard Marks*, *Tom Gayner*, *Mohnish Pabrai*, *Nick Sleep*, *beautifulsoup4*, *docker-compose*, *Production Project Readiness* |
| 57 save-learning silent | 3 | *DuckDB*, *SQLMesh*, *omegaconf* |
| 58 test tooling | 0 | — |
| 59 baseline skills | 0 | — |
| 60 redundant skill loading | 4 | *DuckDB*, *Software Design Principles*, *claude-sdk*, *docker-compose* |
| 61 implement.md reconcile | 2 | *DuckDB*, *claude-sdk* |
| 62 fast-path | 1 | *DuckDB* |
| 63 simplify threshold | 0 | — |

**Observations:**
- Investor-philosophy skills (Howard Marks, Templeton, Nick Sleep, etc.) fire on almost every CLI issue because their descriptions share generic verbs/nouns with Mantle's CLI vocabulary ("lens", "patterns", "scoring", "analysis"). Pure false positives on non-investment work.
- Data-source skills (DuckLake, DuckDB, SQLMesh, Earnings Transcript, etc.) fire on issues that mention generic words like "storage", "query", "pattern". Pure false positives.
- A few edge cases where dropped skills are arguably legitimate: issue 40 `cyclopts`, `Design Review`, `CLI design best practices`. These could be recovered by adding appropriate tags (e.g., `domain/cli` on cyclopts), which is out of scope but noted as a follow-up.
- No test-corpus issue retains a false positive of the type "DuckLake on a CLI fix" → AC #2 satisfied.

## Code design

### Strategy

- `src/mantle/core/skills.py`:
  - Remove lines 775-778 (description-overlap rule inside `detect_skills_from_content`).
  - Remove line 749 (`content_tokens = _tokenize(content_lower)`) — no longer used.
  - Remove `_STOPWORDS` frozenset (L24-52) and `_tokenize` function (L55-57) — no remaining callers in `src/` or `tests/`.
  - Keep `import re` (used elsewhere at L167, L770, L1238).

- `tests/core/test_skills.py`:
  - Delete `test_detect_skills_matches_by_description` (L1401-1414) — its positive assertion no longer holds.
  - Delete `test_detect_skills_no_match_below_threshold` (L1416-1428) — concept of a "threshold" is gone.
  - Add a new test `test_no_false_positive_from_description_tokens` that creates a skill with a "philosophical" description and an issue body with overlapping generic tokens, and asserts the skill is NOT matched (satisfies AC #3 — pins the new rule).

### Fits architecture by

- Internal to `core/skills.py` — no cross-module impact. Matches the core-only-imports-core boundary from `system-design.md`.
- `mantle update-skills` CLI command is a thin wrapper that re-reads `skills_required` after `auto_update_skills` runs, so it picks up the narrower match set with no CLI-side change.
- `mantle compile` consumes `skills_required` verbatim from state/issue YAML; it will compile fewer skills per issue but the compilation pipeline itself is unchanged.

### Does not

- Does not change name/slug/tag matching — those rules stay as-is.
- Does not add tags to existing skills to compensate for lost matches (separate work; noted as follow-up in learnings).
- Does not re-run `update-skills` across past archived issues or mutate their `skills_required`. Archived issues keep their current values.
- Does not introduce IDF or any tf-idf scoring (Approach C, rejected).
- Does not migrate the `_tokenize`/`_STOPWORDS` helpers to a utility module (they are deleted outright since no remaining caller exists).