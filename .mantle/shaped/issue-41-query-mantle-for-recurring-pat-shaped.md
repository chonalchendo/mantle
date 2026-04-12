---
issue: 41
title: Query .mantle/ for recurring patterns — surface themes from learnings and retrospectives
approaches:
- Deterministic pattern analyzer (new core module + CLI + prompt)
- LLM-powered pattern synthesis (prompt-driven clustering via Claude)
- Extend /mantle:query with --patterns flag
chosen_approach: Deterministic pattern analyzer (new core module + CLI + prompt)
appetite: small batch
open_questions:
- Keyword bucketing may be too coarse — may need a follow-up to add LLM clustering
  if themes emerge that keyword lists miss
- 'Should we also scan sessions/ and brainstorms/, or is learnings+issues enough at
  v1? Current choice: learnings+issues only to keep scope tight and match ACs literally'
author: 110059232+chonalchendo@users.noreply.github.com
created: '2026-04-12'
updated: '2026-04-12'
updated_by: 110059232+chonalchendo@users.noreply.github.com
tags:
- type/shaped
- phase/shaping
---

## Approaches evaluated

### A — Deterministic pattern analyzer (chosen)

- **What:** A new `core/patterns.py` loads all `learnings/*.md`, parses YAML frontmatter + section splits (What went well / Harder than expected / Wrong assumptions / Recommendations), buckets items by keyword themes (testing, estimation, scope, tooling, shaping, worktree, ci, skills, other), and joins to `issues/*.md` frontmatter to compute average `confidence_delta` per slice. New `mantle show-patterns` CLI renders a markdown report. New `/mantle:patterns` prompt invokes it.
- **Appetite:** small batch (1–2 days).
- **Tradeoffs:** cheap, deterministic, re-runnable, respects "context should be compiled, not queried" principle. Keyword bucketing is coarse but learnings already have structured section headings, so signal-to-noise is good. No LLM cost.
- **Rabbit holes:** parsing heterogeneous learning files (users may vary section wording). Mitigation: case-insensitive match on the four canonical H2 headings; ignore unknown sections.
- **No-gos:** no LLM call, no schema change, no persistence of pattern reports as notes (one-shot output — compose with `/mantle:distill` if desired), no scanning of sessions/ or brainstorms/ at v1.
- **Side-effect scan:** read-only. No state transitions, no file writes outside stdout.

### B — LLM-powered pattern synthesis

- **What:** `/mantle:patterns` prompt loads learnings and asks Claude to semantically cluster themes.
- **Appetite:** medium batch.
- **Why rejected:** violates "context should be compiled, not queried"; non-deterministic; per-run cost; offers richer themes but ACs 2/3 are satisfiable deterministically with existing structured data. Can be added later as a `--deep` flag if keyword bucketing proves too coarse.

### C — Extend `/mantle:query` with `--patterns` flag

- **What:** overload the existing query command.
- **Appetite:** small batch.
- **Why rejected:** conflates two distinct jobs (ad-hoc Q&A vs recurring-pattern surfacing), violating design principle 8 ("one command, one job"). Query is LLM-based — pattern analysis should be deterministic. A dedicated command is clearer and cheaper.

## Chosen approach — rationale

Approach A is the smallest appetite that satisfies all four ACs, matches two core design principles (compiled-not-queried, one-command-one-job), and leaves room for an LLM upgrade later without lock-in.

## Code design

### Strategy

New module `src/mantle/core/patterns.py`:

- `class Learning(BaseModel)` — `issue: int`, `title: str`, `confidence_delta: int`, `tags: list[str]`, `sections: dict[str, list[str]]` (canonical keys: went_well, harder, wrong_assumptions, recommendations).
- `load_learnings(mantle_dir: Path) -> list[Learning]` — iterate `learnings/*.md`, parse frontmatter via existing `core.vault` helpers, split body by H2 headings.
- `class IssueMeta(BaseModel)` — `number: int`, `slice: list[str]`.
- `load_issues_meta(mantle_dir: Path) -> dict[int, IssueMeta]` — reuse parsing from `core.issues`.
- `THEME_KEYWORDS: dict[str, tuple[str, ...]]` — module-level map: `testing`, `estimation`, `scope`, `tooling`, `shaping`, `worktree`, `ci`, `skills`, `other`.
- `bucket_by_theme(learnings) -> dict[str, list[PatternHit]]` where `PatternHit` carries `(issue, section, text)`.
- `confidence_by_slice(learnings, issues_meta) -> list[SliceStat]` — `SliceStat(slice: str, count: int, avg_delta: float)`.
- `render_report(buckets, slice_stats) -> str` — pure markdown renderer.

New module `src/mantle/cli/patterns.py`:

- `show_patterns()` cyclopts command, registered in `cli/main.py`. Resolves `mantle_dir` via existing helper, composes the three pure functions above, prints report to stdout.

New prompt `claude/commands/mantle/patterns.md`:

- Short, runs `mantle show-patterns`, presents the markdown verbatim, and offers a follow-up `/mantle:distill` if themes are dense.

### Fits architecture by

- `core/patterns.py` only imports from `core/` — respects the core-never-imports-cli boundary (CLAUDE.md "Architecture").
- `cli/patterns.py` depends on core, never the reverse.
- Uses existing frontmatter schemas on `learnings/` and `issues/` — no migration.
- Follows `python-project-conventions` (Google docstrings, 80-char lines, absolute imports, cyclopts).
- Matches design principle 3 ("context should be compiled, not queried") and principle 8 ("one command, one job").
- Tests live at `tests/core/test_patterns.py` and `tests/cli/test_patterns.py`; use `tmp_path` fixtures with synthetic learning/issue files — no real vault access.

### Does not

- Does not call any LLM (AC2/AC3 are satisfiable deterministically).
- Does not change vault file schemas (AC4).
- Does not scan `sessions/`, `brainstorms/`, `research/`, `shaped/` at v1 (learnings + issues cover ACs).
- Does not persist pattern reports as distillation notes (compose with `/mantle:distill` if needed).
- Does not cluster learnings semantically (future `--deep` flag).
- Does not validate user input beyond frontmatter parse errors (CLI boundary responsibility already handled in cyclopts).
- Does not transition state or archive anything — read-only.