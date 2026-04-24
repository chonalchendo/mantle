---
issue: 89
title: 'A/B harness for build pipeline (narrowed: post-hoc comparison; prereq split
  out)'
approaches:
- A — Widen 89 to include per-stage instrumentation
- B — Split into telemetry-prereq + narrow A/B harness (chosen)
- C — Redefine 89 to work with current telemetry (totals only)
chosen_approach: 'B — Split: 89 becomes post-hoc A/B harness; new telemetry-prereq
  issue blocks 89'
appetite: small batch
open_questions:
- 'Prices location: interim O1 (cost-policy.md frontmatter) chosen; pure-YAML migration
  for config.md + cost-policy.md deferred to a separate small-batch issue under v0.24.0'
- Inline-stage costs (shape, plan_stories) resolved in telemetry-prereq, not here
- 'AC-02''s ''per-stage'' requirement: block 89 strictly on telemetry-prereq rather
  than weaken the AC'
- Telemetry-prereq issue not yet created — run /mantle:add-issue next
author: 110059232+chonalchendo@users.noreply.github.com
created: '2026-04-24'
updated: '2026-04-24'
updated_by: 110059232+chonalchendo@users.noreply.github.com
tags:
- type/shaped
- phase/shaping
---

## Context

Issue 89 inherits from issue 75 (replaced) and issue 84 (model-tier presets shipped). The remaining live capability from 75 is an A/B harness that runs the same issue under two model strategies and produces a side-by-side cost + quality report so default recommendations are evidence-based.

Issue 90's retrospective surfaced a hard constraint: build-90's report contained `stories: []` despite a real 25-minute build. `telemetry.group_stories()` only clusters sidechain (Agent-spawned) turns; the build orchestrator runs `shape` and `plan_stories` inline — not as sub-agents — so those turns never enter a cluster. The skeleton baseline at `.mantle/telemetry/baseline-2026-04-21.md` expects per-stage rows (shape, plan_stories, implement, simplify, verify, review, retrospective) that the current code cannot produce.

## Approaches evaluated

### Approach A — Widen 89

Bundle per-stage telemetry instrumentation (stage markers, `stage` dimension on `StoryRun`) together with the A/B harness and report renderer.

- Appetite: large batch (1-2 weeks).
- Pros: one shippable unit.
- Cons: bundles two unrelated concerns (telemetry attribution vs. cost-lever evaluation) into one issue, violating the project's "one command, one job" tier at the issue level. High regression surface inside `core/telemetry.py`. AC count roughly doubles.
- Rabbit hole: the attribution gap from build-90 is undiagnosed; instrumentation design without diagnosis is speculative.

### Approach B — Split into prereq + harness (CHOSEN)

Carve a precondition issue first ("per-stage build telemetry + attribution fix") that:
- Diagnoses the build-90 empty-stories gap.
- Adds a `stage: str | None` dimension to `StoryRun` (or an equivalent aggregation seam).
- Emits stage markers from the build orchestrator when necessary.

Issue 89 then becomes a thin A/B harness that consumes a stage-aware telemetry API and renders a cost + time + quality report.

- Appetite: prereq issue is small-medium; 89 is small.
- Pros: each piece shape-able as a small batch; prereq's telemetry value extends beyond 89 (87/79 cost-reduction work also benefits from per-stage visibility). Clean data-model boundaries.
- Cons: two issues in the v0.23.0 bucket; 89 cannot ship until prereq lands.

### Approach C — Redefine 89 to current telemetry

Drop per-stage entirely. Harness reports totals only (total tokens / wall-clock / cost) plus quality signals from state files.

- Appetite: small batch (1-2 days).
- Pros: ships this week with no instrumentation work.
- Cons: cannot answer "which stage is Sonnet worse at than Opus" — the question the per-stage presets exist to validate. Baseline-2026-04-21 stays permanently skeleton. Per-stage preset choices in `cost-policy.md` remain validated by vibes, not evidence.

## Chosen approach: B (split) with post-hoc execution

Issue 89 is narrowed to an A/B harness only — post-hoc comparison of two existing build files plus state files for quality signals. A new issue ("per-stage build telemetry + attribution fix") is a prerequisite and must be created and shaped before 89 enters `/mantle:plan-stories`.

Within the narrowed 89, three execution models were considered:

- **A.1 Post-hoc only (chosen)** — `mantle ab-build compare <build_1> <build_2>` reads two existing build files + state files, renders the comparison report.
- **A.2 Hybrid** — fresh run + stored baseline. Rejected: likely violates AC-04 (no nested `/mantle:build`) and introduces equivalence problems when two fresh runs cannot target the same already-verified issue.
- **A.3 Live dual-run** — ruled out by the split; this was the Approach-A shape.

A.1 honours AC-04 by construction (no pipeline orchestration) and leaves "equivalence of the two builds" as a user judgement call, which is correct because equivalence is not a mechanical property.

The report surfaces three dimensions the user confirmed as in-scope:

1. **Cost** — total tokens (in/out/cache_read/cache_write) and dollars per strategy.
2. **Time** — wall-clock seconds.
3. **Quality** — retry count per story, blocked-story count, per-AC verification pass/fail, simplifier lines-changed. These signals are already written to `.mantle/stories/*.md` and `.mantle/issues/issue-NN.md` by the existing pipeline — **no new instrumentation needed on the quality side**.

## Appetite

Small batch (1-2 days).

## Code design

### Strategy

One new core module + one CLI command. All read-only; zero writes to `.mantle/` outside the optional report-output path.

- **New: `src/mantle/core/ab_build.py`** — pure functions, no I/O side effects beyond reading existing artefacts.
  - `class Pricing(pydantic.BaseModel, frozen=True)` — per-model `input`/`output`/`cache_read`/`cache_write` dollars-per-million-tokens. Loaded from `.mantle/cost-policy.md` frontmatter (new `prices:` block alongside `presets:`).
  - `class ComparisonRow(pydantic.BaseModel, frozen=True)` — fields `{stage: str | None, metric: str, baseline: float, candidate: float, delta: float}`. Generic enough to represent total rows, per-stage rows (once telemetry-prereq lands), per-story rows, and quality-as-number rows. `stage=None` for rows that don't have a stage attribution today.
  - `class Comparison(pydantic.BaseModel, frozen=True)` — fields `{baseline_label: str, candidate_label: str, cost_rows: tuple[ComparisonRow, ...], quality_rows: tuple[ComparisonRow, ...]}`.
  - `class BuildArtefacts(pydantic.BaseModel, frozen=True)` — `{build_report: telemetry.BuildReport, issue_note: issues.IssueNote, stories: tuple[stories.StoryNote, ...]}` — loaded per-strategy from disk.
  - `compute_cost(report: telemetry.BuildReport, prices: Pricing) -> tuple[int, int, float, float]` — returns `(total_input_tokens, total_output_tokens, total_cost_usd, wall_clock_s)`. Pure function of BuildReport + Pricing. Gracefully returns zeros when `stories == ()`.
  - `collect_quality(issue_note, stories) -> QualityStats` — pure function over already-read state. Returns retry-count, blocked-count, AC pass/fail counts.
  - `build_comparison(baseline: BuildArtefacts, candidate: BuildArtefacts, prices: Pricing) -> Comparison` — top-level orchestrator.
  - `render_markdown(comp: Comparison) -> str` — deterministic string renderer, `inline_snapshot`-friendly.

  Once the telemetry-prereq adds `stage` to `StoryRun`, `compute_cost` grows a `by_stage=True` branch that groups the existing sum. Public surface does not change.

- **New: `src/mantle/cli/ab_build.py`** — one cyclopts command under `GROUPS["review"]`:
  ```python
  def ab_build_compare(
      baseline: Path,
      candidate: Path,
      *,
      issue: int | None = None,
      output: Path | None = None,
  ) -> None
  ```
  Loads both build files, resolves the session JSONL via `telemetry.find_session_file`, parses via `telemetry.read_session` + `telemetry.group_stories`, infers `issue` from frontmatter when unspecified, loads prices via new `core.project.load_prices`, calls `ab_build.build_comparison`, prints via `rich.Console`, optionally writes to `output`.

  Sentinel rejection (AC-03): renderer never emits literal `<fill>`, `TBD`, `pending`, `<x>`, `<y>`. Unit test asserts absence.

- **Extend: `src/mantle/core/project.py`** — add `prices:` to `.mantle/cost-policy.md` frontmatter. New `load_prices(project_root) -> Pricing`. Update bundled `vault-templates/cost-policy.md` with a default prices block (current published rates, commented as "update to match Anthropic rates at measurement time"). No new file; no format change.

### Fits architecture by

- Honours `core` never imports `cli`/`api` — `core/ab_build.py` depends only on `core.telemetry`, `core.issues`, `core.stories`, `core.project`, `core.vault`. Import-linter contract unchanged.
- Extends the existing `cli/builds.py` pattern — that module handles session-id + JSONL + report rendering; `cli/ab_build.py` composes two of those outputs. Same abstraction level.
- Consumes state via existing readers (`issues.list_issues`, `stories.list_stories`, `telemetry.read_session`). No bespoke file-globbing. Acceptance criteria already carry `passes: bool`; no new schema.
- AC-04 holds by construction — the command takes already-written build files as arguments; no path to nest `/mantle:build`.
- Ties prices into `cost-policy.md` alongside presets — one place for all cost configuration. `software-design-principles` skill: "pull complexity downward" — the harness does not re-derive prices.
- Deep-module posture — `build_comparison` is one function with a rich implementation and a narrow 3-argument interface; resists classitis of a `Comparator` class.

### Does not

Derived from the narrowed ACs and architecture boundaries:

- Does not fix the empty-stories attribution bug (belongs to the new telemetry-prereq issue). Harness must render a report even when both inputs have `stories == ()` — it does so by reporting whatever sidechain usage was captured and emitting a "stages: empty — attribution pending" note in the report header.
- Does not emit per-stage rows until the telemetry-prereq adds `stage` to `StoryRun`. The `Comparison` schema has a `stage: str | None` slot for forward compatibility, but the data isn't there yet and the report shows "stage: —" until it is.
- Does not run `/mantle:build` (AC-04 — harness stays out-of-pipeline).
- Does not reset git or `.mantle/` state between runs (no live dual-run).
- Does not capture review or retrospective costs (separate sessions; owned by future session-attribution work).
- Does not migrate `.mantle/` config files to pure YAML (separate concern; see Open Questions).
- Does not update cost-policy.md presets based on report output (user judgement).
- Does not handle malformed build files beyond `telemetry.read_session`'s existing silent-skip behaviour.
- Does not validate that the two builds are "equivalent issues" (user judgement; report header surfaces both issue numbers).
- Does not provide a scanner that finds comparable build pairs (medium-batch scope; user chose small).

## Blockers

Blocks on the new telemetry-prereq issue (not yet created). Create via `/mantle:add-issue`, shape via `/mantle:shape-issue <new>`, then land before 89 enters `/mantle:plan-stories`.

## Open questions

1. **Prices location** — interim: extend `.mantle/cost-policy.md` frontmatter with a `prices:` block. Consistent with current pattern; no new reader path; small-batch stays intact. A follow-up question arose during shaping: should `.mantle/` pure-data config files (config.md, cost-policy.md) migrate to pure YAML? First-principles audit: only those two files have zero-or-pedagogical markdown bodies. Recommendation: defer to a separate small-batch issue under v0.24.0 progressive-disclosure bucket; do not block 89 on it.
2. **Handling of inline-stage costs (shape + plan_stories)** — these run in the orchestrator's own session turns, not sidechains. Resolution belongs to the telemetry-prereq issue. 89 can ship without resolving — renderer shows them as "stage: —" rows at most.
3. **Renderer format** — markdown table only for small-batch. JSON sidecar deferred.
4. **AC updates** — AC-02 (per-stage tokens/seconds/dollar) currently reads "per-stage" as hard-required. If telemetry-prereq lands first, this reads cleanly. If 89 ships before prereq for any reason, AC-02's "per-stage" column is unsatisfiable — either edit the AC to "per-stage when telemetry supports it, totals otherwise" or block 89 strictly on prereq. Recommendation: strict block.