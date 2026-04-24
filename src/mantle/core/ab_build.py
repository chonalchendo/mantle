"""A/B comparison of two build reports — models, computation, rendering.

Pure-function core module. No I/O is performed here; callers supply
already-parsed :class:`telemetry.BuildReport`, :class:`issues.IssueNote`,
and :class:`stories.StoryNote` objects constructed from disk artefacts.
Follow the frozen-pydantic value-object style of ``core/telemetry.py``.
"""

from __future__ import annotations

import pydantic

from mantle.core import issues, project, stories, telemetry  # noqa: TC001

# ── Stage ordering ────────────────────────────────────────────────

_CANONICAL_STAGE_ORDER: tuple[str, ...] = (
    "shape",
    "plan_stories",
    "implement",
    "simplify",
    "verify",
    "review",
    "retrospective",
)

# ── Data models ───────────────────────────────────────────────────


class ComparisonRow(pydantic.BaseModel, frozen=True):
    """A single row in a side-by-side comparison table.

    Used for cost rows, quality-as-number rows, and per-stage-bucketed
    rows.  ``stage=None`` marks totals or quality rows that are not
    attributed to a single pipeline stage.

    Attributes:
        stage: Pipeline stage name, or None for totals / quality rows.
        metric: Human-readable metric name (e.g. ``"tokens_in"``).
        baseline: Metric value for the baseline build.
        candidate: Metric value for the candidate build.
        delta: ``candidate - baseline``.
    """

    stage: str | None
    metric: str
    baseline: float
    candidate: float
    delta: float


class Comparison(pydantic.BaseModel, frozen=True):
    """Side-by-side comparison of two build artefacts.

    Attributes:
        baseline_label: Human-readable label for the baseline build.
        candidate_label: Human-readable label for the candidate build.
        baseline_issue: Issue number for the baseline, or None.
        candidate_issue: Issue number for the candidate, or None.
        cost_rows: Per-stage cost rows plus grand-total rows.
        quality_rows: Quality-metric rows (stories, ACs).
        unpriced_models: Model ids that had no price entry and
            therefore contributed zero cost.
    """

    baseline_label: str
    candidate_label: str
    baseline_issue: int | None
    candidate_issue: int | None
    cost_rows: tuple[ComparisonRow, ...]
    quality_rows: tuple[ComparisonRow, ...]
    unpriced_models: tuple[str, ...]


class BuildArtefacts(pydantic.BaseModel, frozen=True):
    """All parsed artefacts for one side of an A/B comparison.

    Attributes:
        label: Human-readable label (e.g. ``"budget-preset"``).
        issue: Issue number, or None when unknown.
        report: Aggregated build telemetry.
        issue_note: Parsed issue frontmatter, or None when absent.
        stories: Parsed story notes for this issue.
    """

    label: str
    issue: int | None
    report: telemetry.BuildReport
    issue_note: issues.IssueNote | None
    stories: tuple[stories.StoryNote, ...]


class QualityStats(pydantic.BaseModel, frozen=True):
    """Quality statistics derived from issue and story notes.

    Attributes:
        total_stories: Total number of stories.
        blocked_stories: Number of stories with ``status == "blocked"``.
        ac_pass_count: Acceptance criteria that pass.
        ac_fail_count: Acceptance criteria that neither pass nor are waived.
        ac_waived_count: Acceptance criteria explicitly waived.
    """

    total_stories: int
    blocked_stories: int
    ac_pass_count: int
    ac_fail_count: int
    ac_waived_count: int


class CostBreakdown(pydantic.BaseModel, frozen=True):
    """Result of :func:`compute_cost`.

    Each entry in ``per_stage`` is a 7-tuple:
    ``(stage, input_tokens, output_tokens, cache_read_tokens,
    cache_write_tokens, cost_usd, wall_clock_s)``

    ``grand_total`` uses the same layout minus the stage prefix:
    ``(input_tokens, output_tokens, cache_read_tokens,
    cache_write_tokens, cost_usd, wall_clock_s)``

    Attributes:
        per_stage: One entry per occupied stage (including ``None``).
        grand_total: Sum over all stages.
        unpriced_models: Model ids that contributed zero cost because
            they were missing from the prices dict.
    """

    per_stage: tuple[tuple[str | None, int, int, int, int, float, float], ...]
    grand_total: tuple[int, int, int, int, float, float]
    unpriced_models: tuple[str, ...]


# ── Public API ────────────────────────────────────────────────────


def compute_cost(
    report: telemetry.BuildReport,
    prices: dict[str, project.Pricing],
) -> CostBreakdown:
    """Aggregate token usage and cost from a build report.

    Walks ``report.stories``, groups by ``StoryRun.stage`` (using
    ``None`` for unattributed runs), and returns per-stage and
    grand-total cost breakdowns.

    Cost per run is ``sum(usage.<field> * prices[run.model].<field>
    / 1_000_000 for field in (input, output, cache_read, cache_write))``.
    Runs whose model is absent from ``prices`` contribute zero cost and
    are recorded in ``unpriced_models``.

    Args:
        report: Parsed build telemetry.
        prices: Per-model pricing table (USD per million tokens).

    Returns:
        A :class:`CostBreakdown` with per-stage rows, a grand total,
        and the set of model ids that had no price entry.
    """
    # stage -> [input, output, cache_read, cache_write, cost, wall_clock]
    buckets: dict[str | None, list[float]] = {}
    unpriced: set[str] = set()

    for run in report.stories:
        if run.stage not in buckets:
            buckets[run.stage] = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        bucket = buckets[run.stage]
        u = run.usage
        bucket[0] += u.input_tokens
        bucket[1] += u.output_tokens
        bucket[2] += u.cache_read_input_tokens
        bucket[3] += u.cache_creation_input_tokens
        bucket[5] += run.duration_s

        pricing = prices.get(run.model)
        if pricing is None:
            unpriced.add(run.model)
        else:
            cost = (
                u.input_tokens * pricing.input
                + u.output_tokens * pricing.output
                + u.cache_read_input_tokens * pricing.cache_read
                + u.cache_creation_input_tokens * pricing.cache_write
            ) / 1_000_000
            bucket[4] += cost

    per_stage: list[tuple[str | None, int, int, int, int, float, float]] = []
    for stage, vals in buckets.items():
        per_stage.append(
            (
                stage,
                int(vals[0]),
                int(vals[1]),
                int(vals[2]),
                int(vals[3]),
                vals[4],
                vals[5],
            )
        )

    grand: list[float] = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    for vals in buckets.values():
        for i in range(6):
            grand[i] += vals[i]

    grand_total: tuple[int, int, int, int, float, float] = (
        int(grand[0]),
        int(grand[1]),
        int(grand[2]),
        int(grand[3]),
        grand[4],
        grand[5],
    )

    return CostBreakdown(
        per_stage=tuple(per_stage),
        grand_total=grand_total,
        unpriced_models=tuple(sorted(unpriced)),
    )


def collect_quality(
    issue_note: issues.IssueNote | None,
    story_notes: tuple[stories.StoryNote, ...],
) -> QualityStats:
    """Derive quality statistics from issue and story notes.

    Counts blocked stories and AC pass/fail/waived states.  When
    ``issue_note`` is ``None`` all AC counts are zero.

    Args:
        issue_note: Parsed issue frontmatter, or None.
        story_notes: Parsed story notes for this issue.

    Returns:
        Aggregated :class:`QualityStats`.
    """
    total = len(story_notes)
    blocked = sum(1 for s in story_notes if s.status == "blocked")

    if issue_note is None:
        return QualityStats(
            total_stories=total,
            blocked_stories=blocked,
            ac_pass_count=0,
            ac_fail_count=0,
            ac_waived_count=0,
        )

    pass_count = 0
    fail_count = 0
    waived_count = 0
    for ac in issue_note.acceptance_criteria:
        if ac.waived:
            waived_count += 1
        elif ac.passes:
            pass_count += 1
        else:
            fail_count += 1

    return QualityStats(
        total_stories=total,
        blocked_stories=blocked,
        ac_pass_count=pass_count,
        ac_fail_count=fail_count,
        ac_waived_count=waived_count,
    )


def build_comparison(
    baseline: BuildArtefacts,
    candidate: BuildArtefacts,
    prices: dict[str, project.Pricing],
) -> Comparison:
    """Build a side-by-side Comparison from two BuildArtefacts.

    Calls :func:`compute_cost` and :func:`collect_quality` on both
    sides, then assembles :class:`ComparisonRow` objects in canonical
    stage order.

    Args:
        baseline: Artefacts for the baseline (control) build.
        candidate: Artefacts for the candidate build.
        prices: Per-model pricing table.

    Returns:
        A fully-assembled :class:`Comparison`.
    """
    b_cost = compute_cost(baseline.report, prices)
    c_cost = compute_cost(candidate.report, prices)
    b_quality = collect_quality(baseline.issue_note, baseline.stories)
    c_quality = collect_quality(candidate.issue_note, candidate.stories)

    # Index per_stage by stage key
    b_stage: dict[
        str | None, tuple[str | None, int, int, int, int, float, float]
    ] = {row[0]: row for row in b_cost.per_stage}
    c_stage: dict[
        str | None, tuple[str | None, int, int, int, int, float, float]
    ] = {row[0]: row for row in c_cost.per_stage}

    all_named_stages: set[str] = set()
    has_none = False
    for key in list(b_stage) + list(c_stage):
        if key is None:
            has_none = True
        else:
            all_named_stages.add(key)

    # Emit rows in canonical order, then Unattributed if present
    cost_rows: list[ComparisonRow] = []
    _zero: tuple[str | None, int, int, int, int, float, float] = (
        None,
        0,
        0,
        0,
        0,
        0.0,
        0.0,
    )

    for stage in _CANONICAL_STAGE_ORDER:
        if stage not in all_named_stages:
            continue
        b_row = b_stage.get(stage, _zero)
        c_row = c_stage.get(stage, _zero)
        cost_rows.extend(_stage_metric_rows(stage, b_row, c_row))

    if has_none:
        b_row = b_stage.get(None, _zero)
        c_row = c_stage.get(None, _zero)
        cost_rows.extend(_stage_metric_rows(None, b_row, c_row))

    # Grand totals — stage=None, metric starts with "total_"
    b_gt = b_cost.grand_total
    c_gt = c_cost.grand_total
    cost_rows.extend(
        [
            ComparisonRow(
                stage=None,
                metric="total_tokens_in",
                baseline=float(b_gt[0]),
                candidate=float(c_gt[0]),
                delta=float(c_gt[0] - b_gt[0]),
            ),
            ComparisonRow(
                stage=None,
                metric="total_tokens_out",
                baseline=float(b_gt[1]),
                candidate=float(c_gt[1]),
                delta=float(c_gt[1] - b_gt[1]),
            ),
            ComparisonRow(
                stage=None,
                metric="total_wall_clock_s",
                baseline=b_gt[5],
                candidate=c_gt[5],
                delta=c_gt[5] - b_gt[5],
            ),
            ComparisonRow(
                stage=None,
                metric="total_cost_usd",
                baseline=b_gt[4],
                candidate=c_gt[4],
                delta=c_gt[4] - b_gt[4],
            ),
        ]
    )

    # Quality rows
    quality_rows: list[ComparisonRow] = [
        ComparisonRow(
            stage=None,
            metric="total_stories",
            baseline=float(b_quality.total_stories),
            candidate=float(c_quality.total_stories),
            delta=float(c_quality.total_stories - b_quality.total_stories),
        ),
        ComparisonRow(
            stage=None,
            metric="blocked_stories",
            baseline=float(b_quality.blocked_stories),
            candidate=float(c_quality.blocked_stories),
            delta=float(c_quality.blocked_stories - b_quality.blocked_stories),
        ),
        ComparisonRow(
            stage=None,
            metric="ac_pass_count",
            baseline=float(b_quality.ac_pass_count),
            candidate=float(c_quality.ac_pass_count),
            delta=float(c_quality.ac_pass_count - b_quality.ac_pass_count),
        ),
        ComparisonRow(
            stage=None,
            metric="ac_fail_count",
            baseline=float(b_quality.ac_fail_count),
            candidate=float(c_quality.ac_fail_count),
            delta=float(c_quality.ac_fail_count - b_quality.ac_fail_count),
        ),
        ComparisonRow(
            stage=None,
            metric="ac_waived_count",
            baseline=float(b_quality.ac_waived_count),
            candidate=float(c_quality.ac_waived_count),
            delta=float(c_quality.ac_waived_count - b_quality.ac_waived_count),
        ),
    ]

    all_unpriced = tuple(
        sorted(set(b_cost.unpriced_models) | set(c_cost.unpriced_models))
    )

    return Comparison(
        baseline_label=baseline.label,
        candidate_label=candidate.label,
        baseline_issue=baseline.issue,
        candidate_issue=candidate.issue,
        cost_rows=tuple(cost_rows),
        quality_rows=tuple(quality_rows),
        unpriced_models=all_unpriced,
    )


def render_markdown(comp: Comparison) -> str:
    """Render a Comparison as a deterministic markdown string.

    Output sections:
      1. Header with baseline/candidate labels and issue numbers.
      2. Cost tables grouped by stage (``## Cost — <stage>``), plus
         ``## Cost — Unattributed`` for ``stage=None`` cost rows that
         are not grand-total rows.
      3. ``## Grand Totals`` section.
      4. ``## Quality`` section.

    Numerical formatting:
      - Integer counts: ``{n}``
      - USD: ``{x:.4f}``
      - Seconds: ``{x:.1f}``
      - Delta: explicit ``+`` for positives (e.g. ``{x:+.4f}``)

    Sentinel cleanliness (AC-03): never emits ``<fill>``, ``TBD``,
    ``pending``, ``<x>``, or ``<y>``.  All cells show real numbers
    even when zero.

    Args:
        comp: Assembled comparison object.

    Returns:
        Full markdown report as a string ending with a newline.
    """
    lines: list[str] = []

    # ── Header ────────────────────────────────────────────────────
    lines.append("# A/B build comparison")
    lines.append("")
    lines.append(f"- baseline: {comp.baseline_label}")
    lines.append(f"- candidate: {comp.candidate_label}")
    lines.append(f"- issues: {comp.baseline_issue} vs {comp.candidate_issue}")
    lines.append("")

    # Partition cost rows: stage rows vs grand-total rows
    total_rows = [r for r in comp.cost_rows if r.metric.startswith("total_")]
    stage_rows = [
        r for r in comp.cost_rows if not r.metric.startswith("total_")
    ]

    # Group stage rows by stage key
    rows_by_stage: dict[str | None, list[ComparisonRow]] = {}
    for row in stage_rows:
        rows_by_stage.setdefault(row.stage, []).append(row)

    # Emit named stages in canonical order
    for stage_name in _CANONICAL_STAGE_ORDER:
        if stage_name not in rows_by_stage:
            continue
        lines.append(f"## Cost — {stage_name}")
        lines.append("")
        _render_cost_table(lines, rows_by_stage[stage_name])
        lines.append("")

    # Emit Unattributed bucket
    if None in rows_by_stage:
        lines.append("## Cost — Unattributed")
        lines.append("")
        _render_cost_table(lines, rows_by_stage[None])
        lines.append("")

    # ── Grand Totals ───────────────────────────────────────────────
    lines.append("## Grand Totals")
    lines.append("")
    lines.append("| Metric | Baseline | Candidate | Δ |")
    lines.append("|--------|----------|-----------|---|")
    for row in total_rows:
        if row.metric in ("total_cost_usd",):
            b_str = f"{row.baseline:.4f}"
            c_str = f"{row.candidate:.4f}"
            d_str = f"{row.delta:+.4f}"
        elif row.metric == "total_wall_clock_s":
            b_str = f"{row.baseline:.1f}"
            c_str = f"{row.candidate:.1f}"
            d_str = f"{row.delta:+.1f}"
        else:
            b_str = f"{int(row.baseline)}"
            c_str = f"{int(row.candidate)}"
            d_str = f"{row.delta:+.0f}"
        lines.append(f"| {row.metric} | {b_str} | {c_str} | {d_str} |")
    lines.append("")

    # ── Quality ───────────────────────────────────────────────────
    lines.append("## Quality")
    lines.append("")
    lines.append("| Metric | Baseline | Candidate | Δ |")
    lines.append("|--------|----------|-----------|---|")
    for row in comp.quality_rows:
        b_str = f"{int(row.baseline)}"
        c_str = f"{int(row.candidate)}"
        d_str = f"{row.delta:+.0f}"
        lines.append(f"| {row.metric} | {b_str} | {c_str} | {d_str} |")
    lines.append("")

    # ── Unpriced warning ──────────────────────────────────────────
    if comp.unpriced_models:
        model_list = ", ".join(comp.unpriced_models)
        lines.append(f"> Warning: unpriced models encountered: {model_list}")
        lines.append("")

    return "\n".join(lines)


# ── Internal helpers ──────────────────────────────────────────────


def _stage_metric_rows(
    stage: str | None,
    b_row: tuple[str | None, int, int, int, int, float, float],
    c_row: tuple[str | None, int, int, int, int, float, float],
) -> list[ComparisonRow]:
    """Build the four metric rows for one stage.

    Args:
        stage: Stage name or None for Unattributed.
        b_row: Baseline per-stage tuple.
        c_row: Candidate per-stage tuple.

    Returns:
        Four ComparisonRow objects for tokens_in, tokens_out,
        wall_clock_s, and cost_usd.
    """
    # Indices: 0=stage, 1=inp, 2=out, 3=cr, 4=cw, 5=cost, 6=wall
    b_inp, b_out, b_cost, b_wall = (
        float(b_row[1]),
        float(b_row[2]),
        b_row[5],
        b_row[6],
    )
    c_inp, c_out, c_cost, c_wall = (
        float(c_row[1]),
        float(c_row[2]),
        c_row[5],
        c_row[6],
    )
    return [
        ComparisonRow(
            stage=stage,
            metric="tokens_in",
            baseline=b_inp,
            candidate=c_inp,
            delta=c_inp - b_inp,
        ),
        ComparisonRow(
            stage=stage,
            metric="tokens_out",
            baseline=b_out,
            candidate=c_out,
            delta=c_out - b_out,
        ),
        ComparisonRow(
            stage=stage,
            metric="wall_clock_s",
            baseline=b_wall,
            candidate=c_wall,
            delta=c_wall - b_wall,
        ),
        ComparisonRow(
            stage=stage,
            metric="cost_usd",
            baseline=b_cost,
            candidate=c_cost,
            delta=c_cost - b_cost,
        ),
    ]


def _render_cost_table(
    lines: list[str],
    rows: list[ComparisonRow],
) -> None:
    """Append a cost table section (header + rows) to lines in-place.

    Args:
        lines: Accumulator list to append to.
        rows: ComparisonRows for this stage.
    """
    lines.append("| Metric | Baseline | Candidate | Δ |")
    lines.append("|--------|----------|-----------|---|")
    for row in rows:
        if row.metric == "cost_usd":
            b_str = f"{row.baseline:.4f}"
            c_str = f"{row.candidate:.4f}"
            d_str = f"{row.delta:+.4f}"
        elif row.metric == "wall_clock_s":
            b_str = f"{row.baseline:.1f}"
            c_str = f"{row.candidate:.1f}"
            d_str = f"{row.delta:+.1f}"
        else:
            b_str = f"{int(row.baseline)}"
            c_str = f"{int(row.candidate)}"
            d_str = f"{row.delta:+.0f}"
        lines.append(f"| {row.metric} | {b_str} | {c_str} | {d_str} |")
