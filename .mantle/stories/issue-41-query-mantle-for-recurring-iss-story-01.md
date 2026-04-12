---
issue: 41
title: Core patterns module — load learnings, bucket by theme, confidence trend, render
  report
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a developer, I want a pure-Python analysis module that turns accumulated learning notes into a grouped pattern report so that the CLI and prompt layers can surface trends without duplicating parsing logic.

## Depends On

None — independent (foundation story).

## Approach

Follow the pattern of `src/mantle/core/learning.py` and `src/mantle/core/issues.py`: a `pydantic.BaseModel` data class, a small number of public functions, internal helpers below a `# ── Internal helpers ──` banner. All work is deterministic — no LLM, no network, no filesystem writes. Parsing reuses `core.learning.list_learnings` / `core.learning.load_learning` and `core.issues.load_issue` / `core.issues.list_issues` so this module owns only the analysis logic, not the I/O primitives.

## Implementation

### src/mantle/core/patterns.py (new file)

Public API:

- `class PatternHit(BaseModel, frozen=True)` — `issue: int`, `section: str` (one of `"harder"`, `"wrong_assumptions"`, `"recommendations"`), `text: str` (one bullet, trimmed).
- `class SliceStat(BaseModel, frozen=True)` — `slice: str`, `count: int`, `avg_delta: float`.
- `class PatternReport(BaseModel, frozen=True)` — `total_learnings: int`, `themes: dict[str, tuple[PatternHit, ...]]`, `slice_stats: tuple[SliceStat, ...]`.
- `def analyze_patterns(project_dir: Path) -> PatternReport` — entry point that calls `core.learning.list_learnings`, loads each via `core.learning.load_learning`, joins against issue metadata from `core.issues`, and returns a `PatternReport`.
- `def render_report(report: PatternReport) -> str` — deterministic markdown renderer.

Internal helpers:

- `_SECTION_PATTERNS: dict[str, re.Pattern]` — compiled regexes for the four H2 headings (case-insensitive, tolerating the canonical wording used in retrospective.md: `## What went well`, `## Harder than expected`, `## Wrong assumptions`, `## Recommendations`).
- `_split_sections(body: str) -> dict[str, list[str]]` — returns lists of bullet items (lines starting with `- ` after stripping Markdown) keyed by canonical names `went_well`, `harder`, `wrong_assumptions`, `recommendations`. Unmatched headings are dropped silently.
- `_THEME_KEYWORDS: dict[str, tuple[str, ...]]` — module-level mapping from theme name to keyword lowercase substrings. Themes and sample keywords:
  - `testing` → `test`, `pytest`, `fixture`, `mock`, `coverage`
  - `estimation` → `estimat`, `appetite`, `took longer`, `underestim`, `overestim`
  - `scope` → `scope`, `out of scope`, `scope creep`, `out-of-scope`
  - `tooling` → `cli`, `uv`, `just`, `prek`, `installed`, `command not found`
  - `shaping` → `shape`, `approach`, `rabbit hole`, `tradeoff`
  - `worktree` → `worktree`, `isolation`, `merge`, `branch`
  - `ci` → ` ci `, `github action`, `workflow`, `publish`
  - `skills` → `skill`, `vault`
  - `other` is the fallback bucket when nothing matches.
- `_theme_for(text: str) -> str` — lowercase-match each keyword list in declaration order, return first hit, else `"other"`.
- `_bucket_by_theme(learnings: Iterable[tuple[LearningNote, str]]) -> dict[str, list[PatternHit]]` — for sections `harder`, `wrong_assumptions`, `recommendations`, produce `PatternHit`s and bucket. Sort inside each bucket by issue number ascending then section then text.
- `_confidence_by_slice(notes_with_slices: Iterable[tuple[LearningNote, tuple[str, ...]]]) -> list[SliceStat]` — average `int(confidence_delta)` per slice (slices derived from `IssueNote.slice` joined on issue number). Sorted by `avg_delta` ascending (most-painful first) then slice name. Excludes learnings whose parent issue can't be located.

#### Design decisions

- **No LLM, no scan widening**: Only `learnings/` + `issues/` per shaping. Keeps the module deterministic and cheap.
- **Keyword bucketing over clustering**: Matches the appetite. If coarseness bites, a `--deep` LLM mode can be added later without disturbing this public surface.
- **Reuse I/O primitives**: `load_learning` / `load_issue` already handle frontmatter parsing, tag sanitisation, and path discovery — don't re-implement.
- **Frozen Pydantic models**: Mirrors project convention for data carriers (see `LearningNote`, `IssueNote`).
- **Markdown rendering lives in core**: `render_report` is pure — CLI layer just prints.

### Report format (produced by `render_report`)

```
# Recurring Patterns

Based on N learnings.

## Themes

### Testing (3 hits)
- issue 47 (harder): full description
- ...

### Estimation (2 hits)
...

## Confidence trend by slice

| Slice | Learnings | Avg Δ confidence |
| --- | ---: | ---: |
| core | 4 | -0.5 |
| cli | 3 | +1.0 |

_Slices with no matched issue are omitted._
```

Empty themes are omitted. If no learnings exist, `render_report` returns `"No learnings found — run /mantle:retrospective after an issue to start capturing patterns.\n"`.

## Tests

### tests/core/test_patterns.py (new file)

Use `tmp_path` with a synthetic `.mantle/` tree (create `.mantle/learnings/issue-NN-*.md` and `.mantle/issues/issue-NN-*.md` with minimal frontmatter). Never touch the real vault.

- **test_analyze_patterns_empty_vault_returns_zero_learnings**: no `learnings/` dir → `PatternReport(total_learnings=0, themes={}, slice_stats=())`.
- **test_split_sections_extracts_bullets_under_canonical_headings**: a learning body with all four H2s plus bullet lists → `_split_sections` returns the right lists per canonical key.
- **test_split_sections_ignores_unknown_headings**: unknown H2 → not in output.
- **test_theme_for_buckets_testing_keywords**: texts containing "pytest fixture" / "test coverage" → `"testing"`.
- **test_theme_for_falls_back_to_other**: text with no matching keyword → `"other"`.
- **test_analyze_patterns_buckets_across_multiple_learnings**: two learnings with different themes → themes dict contains both, each with the correct `PatternHit`s in issue-number order.
- **test_analyze_patterns_drops_went_well_section**: content under `## What went well` never produces a `PatternHit`.
- **test_confidence_by_slice_averages_per_slice**: three learnings, one issue each with overlapping slices, deltas `+2`, `-1`, `+0` → correct `SliceStat.avg_delta` per slice, sorted ascending.
- **test_confidence_by_slice_ignores_unmatched_issue**: learning whose issue file is missing contributes to none of the slice stats (doesn't crash).
- **test_render_report_produces_markdown_with_themes_and_trend_table**: given a known `PatternReport`, output contains `## Themes`, per-theme `### ...` headings, a `| Slice |` header row, and the correct bullet lines.
- **test_render_report_empty_learnings_returns_guidance_message**: `PatternReport(total_learnings=0, ...)` → returns the "No learnings found" guidance string.