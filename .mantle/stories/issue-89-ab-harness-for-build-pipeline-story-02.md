---
issue: 89
title: Core ab_build module — comparison models, compute_cost, build_comparison, render_markdown
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a Mantle user evaluating budget vs quality presets, I want a pure, tested core function that turns two build reports into a side-by-side comparison so the CLI layer stays thin and the comparison logic stays testable in isolation.

## Depends On

Story 1 — consumes `project.Pricing` and `project.load_prices`.

## Approach

Introduce `src/mantle/core/ab_build.py` as a pure-function core module that imports only `core.telemetry`, `core.issues`, `core.stories`, and `core.project`. No I/O beyond reading already-on-disk artefacts through those existing readers. Follow the frozen-pydantic-value-object style already established in `core/telemetry.py` (`StoryRun`, `BuildReport`) and the deterministic-string-renderer style of `telemetry.render_report` for `render_markdown`. Build on top of the story-1 `Pricing` contract.

## Implementation

### src/mantle/core/ab_build.py (new file)

Public API (in this order):

- `class ComparisonRow(pydantic.BaseModel, frozen=True)` — fields: `stage: str | None`, `metric: str`, `baseline: float`, `candidate: float`, `delta: float`. Generic enough for cost rows, quality-as-number rows, and per-stage-bucketed rows. `stage=None` marks totals or quality rows.

- `class Comparison(pydantic.BaseModel, frozen=True)` — fields: `baseline_label: str`, `candidate_label: str`, `baseline_issue: int | None`, `candidate_issue: int | None`, `cost_rows: tuple[ComparisonRow, ...]`, `quality_rows: tuple[ComparisonRow, ...]`.

- `class BuildArtefacts(pydantic.BaseModel, frozen=True)` — fields: `label: str`, `issue: int | None`, `report: telemetry.BuildReport`, `issue_note: issues.IssueNote | None`, `stories: tuple[stories.StoryNote, ...]`.

- `class QualityStats(pydantic.BaseModel, frozen=True)` — fields: `total_stories: int`, `blocked_stories: int`, `ac_pass_count: int`, `ac_fail_count: int`, `ac_waived_count: int`.

- `def compute_cost(report: telemetry.BuildReport, prices: dict[str, project.Pricing]) -> tuple[dict[str | None, tuple[int, int, int, int, float, float]], tuple[int, int, int, int, float, float]]`. Walks `report.stories`, groups by `StoryRun.stage` (using `None` as the bucket key for unattributed runs), and returns `(per_stage_totals, grand_total)` where each tuple contains `(input_tokens, output_tokens, cache_read_tokens, cache_write_tokens, cost_usd, wall_clock_s)`. Cost is computed per `StoryRun` as `sum(usage.<field> * prices[run.model].<field> / 1_000_000 for field in (input, output, cache_read, cache_write))` using `run.model` as the lookup key; runs whose `model` string is missing from the `prices` dict contribute zero cost (not a hard error — keeps pre-92 mixed-model builds renderable) but the zero contribution is recorded on a sidechannel returned via a second value `unpriced_models: tuple[str, ...]`. Revise the signature to return a dedicated `CostBreakdown(pydantic.BaseModel, frozen=True)` with fields `{per_stage: tuple[tuple[str | None, int, int, int, int, float, float], ...], grand_total: tuple[int, int, int, int, float, float], unpriced_models: tuple[str, ...]}` to keep call sites typed. Wall-clock per stage is `sum(run.duration_s)`.

- `def collect_quality(issue_note: issues.IssueNote | None, stories: tuple[stories.StoryNote, ...]) -> QualityStats`. Pure function over already-read state. Counts `total_stories = len(stories)`, `blocked_stories = sum(1 for s in stories if s.status == "blocked")`, plus AC counts from `issue_note.acceptance_criteria` (use the existing `.passes` / `.waived` boolean fields). Returns `QualityStats(0, 0, 0, 0, 0)` when `issue_note` is None.

- `def build_comparison(baseline: BuildArtefacts, candidate: BuildArtefacts, prices: dict[str, project.Pricing]) -> Comparison`. Top-level orchestrator. Calls `compute_cost` on both sides, `collect_quality` on both sides, then assembles `ComparisonRow`s:
  - For each unique stage across both builds (known-stages-first in fixed order `("shape", "plan_stories", "implement", "simplify", "verify", "review", "retrospective")`, then an Unattributed bucket for `stage=None`): emit one row each for `tokens_in`, `tokens_out`, `wall_clock_s`, `cost_usd`. A row's `baseline`/`candidate` is `0.0` when that side has no data for that stage (legitimate zero, not a placeholder).
  - Grand totals: four more `ComparisonRow`s with `stage=None`, metrics `total_tokens_in`, `total_tokens_out`, `total_wall_clock_s`, `total_cost_usd`.
  - Quality rows: `ComparisonRow`s with `stage=None` and metrics `total_stories`, `blocked_stories`, `ac_pass_count`, `ac_fail_count`, `ac_waived_count`.
  - `delta = candidate - baseline` for every row.
  - `baseline_label` / `candidate_label` are copied from the `BuildArtefacts.label` inputs; `baseline_issue` / `candidate_issue` from `BuildArtefacts.issue`.

- `def render_markdown(comp: Comparison) -> str`. Deterministic, snapshot-friendly. Emits:
  1. A header: `# A/B build comparison` + two lines `- baseline: <label>` / `- candidate: <label>` + `- issues: <baseline_issue> vs <candidate_issue>` (printing literal `None` is acceptable).
  2. A cost table grouped by stage (one `## Cost — <stage>` subsection per occupied stage, plus a `## Cost — Unattributed` subsection if any rows have `stage=None` that aren't grand-total rows). Each table has columns `Metric | Baseline | Candidate | Δ` and one row per `ComparisonRow` under that stage.
  3. A `## Grand Totals` section.
  4. A `## Quality` section.
  - All numerical cells are rendered with fixed precision: integers as `{n}`, floats as `{x:.4f}` for dollars, `{x:.1f}` for seconds, `{x}` for plain counts. `delta` uses explicit `+` for positives (`{x:+.4f}` etc).
  - **Sentinel cleanliness (AC-03)**: never emits the literal substrings `<fill>`, `TBD`, `pending`, `<x>`, `<y>`. Writes the actual numbers even when they are zero.

#### Design decisions

- **Value objects + top-level functions, not a `Comparator` class**: follows the `core/telemetry.py` posture — frozen models for data, module-level functions for transformations. Resists classitis.
- **Unpriced models are a soft fallback, not a hard error**: older builds may list models by id strings that don't match the current `prices` dict. The renderer surfaces `unpriced_models` as a trailing warning line (`> ⚠️ unpriced models encountered: ...`) so the user knows the zero came from a missing rate, not a real zero-cost run. This keeps zero-valued cells legitimate under AC-03.
- **Fixed stage order for rendering**: matches the build pipeline's canonical sequence so reports are readable left-to-right. Stages absent from both sides are simply not rendered.

## Tests

### tests/core/test_ab_build.py (new file)

- **test_compute_cost_sums_usage_against_prices**: given a `BuildReport` with two `StoryRun`s of known `model` + `usage`, and a hand-built `prices` dict, `compute_cost()` returns per-stage and grand-total tuples whose numbers equal the handcalculated values. Use `dirty-equals.IsPartialDict` if needed to keep the assertion focused.
- **test_compute_cost_groups_by_stage_with_none_bucket**: three `StoryRun`s — two with `stage="implement"`, one with `stage=None` — return a dict whose keys are exactly `{"implement", None}` and whose bucket totals match.
- **test_compute_cost_reports_unpriced_models**: a `StoryRun` with `model="some-new-model"` not present in the prices dict lands in `unpriced_models`; its cost contribution to the grand total is `0.0`.
- **test_collect_quality_counts_blocked_and_ac_states**: a hand-built `IssueNote` with 3 passing, 1 failing, 1 waived AC plus 4 `StoryNote`s (1 blocked) returns `QualityStats(4, 1, 3, 1, 1)`.
- **test_collect_quality_handles_none_issue_note**: with `issue_note=None` and empty `stories`, returns all-zero `QualityStats`.
- **test_build_comparison_produces_stage_grouped_rows_plus_totals**: full roundtrip with two mini `BuildArtefacts` — assert the returned `Comparison.cost_rows` contains (a) per-stage rows for every stage occupied on either side, (b) an `Unattributed` bucket when a `StoryRun.stage=None` is present, and (c) four grand-total rows at the end. Use `inline_snapshot` for the rendered markdown.
- **test_render_markdown_emits_stage_subsections_in_canonical_order**: `inline_snapshot` the full rendered output for a handcrafted `Comparison` spanning `shape`, `implement`, and `verify` plus an Unattributed bucket. Verify the subsections appear in that order.
- **test_render_markdown_never_emits_sentinels**: render a `Comparison` where multiple rows have zero values; assert the output string does not contain any of `<fill>`, `TBD`, `pending`, `<x>`, `<y>` (AC-03).
- **test_render_markdown_surfaces_unpriced_warning**: pass an `unpriced_models=("ancient-model",)` — assert the warning line appears in the output.
- **test_build_comparison_empty_stories_on_both_sides**: both `BuildArtefacts` have `report.stories == ()`; `Comparison.cost_rows` contains only the grand-total rows (all zeros), `quality_rows` still populated, `render_markdown` still returns sentinel-free text.

Fixture requirements: all tests construct `telemetry.BuildReport`, `telemetry.StoryRun`, `telemetry.Usage`, `issues.IssueNote`, `stories.StoryNote`, and `project.Pricing` objects in-memory. No filesystem, no `tmp_path` needed for the core-level tests. Follow `pydantic-project-conventions` — frozen inputs, explicit construction.