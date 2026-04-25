"""Tests for mantle.core.ab_build — comparison models and transforms."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from inline_snapshot import snapshot

from mantle.core import (
    ab_build,
    acceptance,
    issues,
    project,
    stories,
    telemetry,
)

# ── Shared construction helpers ──────────────────────────────────


_T0 = datetime(2025, 1, 1, 0, 0, 0, tzinfo=UTC)
_T1 = datetime(2025, 1, 1, 1, 0, 0, tzinfo=UTC)


def _usage(
    inp: int = 100,
    out: int = 50,
    cache_read: int = 0,
    cache_write: int = 0,
) -> telemetry.Usage:
    return telemetry.Usage(
        input_tokens=inp,
        output_tokens=out,
        cache_read_input_tokens=cache_read,
        cache_creation_input_tokens=cache_write,
    )


def _story_run(
    stage: str | None = "implement",
    model: str = "sonnet",
    inp: int = 100,
    out: int = 50,
    cache_read: int = 0,
    cache_write: int = 0,
    duration_s: float = 10.0,
) -> telemetry.StoryRun:
    return telemetry.StoryRun(
        story_id=1,
        model=model,
        started=_T0,
        finished=_T1,
        duration_s=duration_s,
        usage=_usage(inp, out, cache_read, cache_write),
        turn_count=5,
        stage=stage,
    )


def _build_report(
    stories_seq: tuple[telemetry.StoryRun, ...],
) -> telemetry.BuildReport:
    return telemetry.BuildReport(
        session_id="sess-abc",
        started=_T0,
        finished=_T1,
        stories=stories_seq,
    )


def _prices(
    inp: float = 3.0,
    out: float = 15.0,
    cache_read: float = 0.3,
    cache_write: float = 3.75,
) -> dict[str, project.Pricing]:
    return {
        "sonnet": project.Pricing(
            input=inp,
            output=out,
            cache_read=cache_read,
            cache_write=cache_write,
        )
    }


def _criterion(
    id: str,
    passes: bool = True,
    waived: bool = False,
) -> acceptance.AcceptanceCriterion:
    return acceptance.AcceptanceCriterion(
        id=id, text=f"criterion {id}", passes=passes, waived=waived
    )


def _issue_note(
    criteria: tuple[acceptance.AcceptanceCriterion, ...],
) -> issues.IssueNote:
    return issues.IssueNote(
        title="Test Issue",
        slice=("core",),
        acceptance_criteria=criteria,
    )


def _story_note(status: str = "completed") -> stories.StoryNote:
    return stories.StoryNote(issue=89, title="Story", status=status)


def _build_artefacts(
    label: str = "baseline",
    issue: int | None = 89,
    story_runs: tuple[telemetry.StoryRun, ...] = (),
    issue_note: issues.IssueNote | None = None,
    story_notes: tuple[stories.StoryNote, ...] = (),
) -> ab_build.BuildArtefacts:
    return ab_build.BuildArtefacts(
        label=label,
        issue=issue,
        report=_build_report(story_runs),
        issue_note=issue_note,
        stories=story_notes,
    )


# ── compute_cost ─────────────────────────────────────────────────


def test_compute_cost_sums_usage_against_prices() -> None:
    """compute_cost returns correct per-stage and grand-total cost."""
    run = _story_run(stage="implement", inp=1_000_000, out=500_000)
    report = _build_report((run,))
    prices = _prices(inp=3.0, out=15.0, cache_read=0.3, cache_write=3.75)

    result = ab_build.compute_cost(report, prices)

    # 1_000_000 * 3.0 / 1_000_000 = 3.0
    # 500_000 * 15.0 / 1_000_000 = 7.5
    # grand total cost = 10.5
    assert result.grand_total[4] == 10.5
    assert result.grand_total[0] == 1_000_000  # input tokens
    assert result.grand_total[1] == 500_000  # output tokens


def test_compute_cost_groups_by_stage_with_none_bucket() -> None:
    """compute_cost groups runs by stage and creates None bucket for unattributed."""
    runs = (
        _story_run(stage="implement", inp=100, out=50, duration_s=10.0),
        _story_run(stage="implement", inp=200, out=80, duration_s=20.0),
        _story_run(stage=None, inp=50, out=25, duration_s=5.0),
    )
    report = _build_report(runs)
    prices = _prices()

    result = ab_build.compute_cost(report, prices)

    stage_keys = {row[0] for row in result.per_stage}
    assert stage_keys == {"implement", None}

    impl_row = next(r for r in result.per_stage if r[0] == "implement")
    assert impl_row[1] == 300  # input tokens: 100 + 200
    assert impl_row[2] == 130  # output tokens: 50 + 80

    none_row = next(r for r in result.per_stage if r[0] is None)
    assert none_row[1] == 50  # input tokens

    assert result.grand_total[0] == 350  # total input: 100+200+50


def test_compute_cost_reports_unpriced_models() -> None:
    """Runs with unknown model land in unpriced_models, cost is 0."""
    run = _story_run(
        stage="implement", model="some-new-model", inp=1000, out=500
    )
    report = _build_report((run,))
    prices = _prices()  # only "sonnet" priced

    result = ab_build.compute_cost(report, prices)

    assert "some-new-model" in result.unpriced_models
    assert result.grand_total[4] == 0.0  # zero cost contribution


def test_compute_cost_resolves_full_model_ids_via_tier_substring() -> None:
    """Full Anthropic model ids (``claude-opus-4-7``) match tier-keyed prices.

    Build telemetry stores full ids; ``cost-policy.md`` keys prices by
    tier (``opus``/``sonnet``/``haiku``). The resolver bridges the two
    so the cost column never silently falls to $0 on real builds.
    """
    runs = (
        _story_run(
            stage="implement",
            model="claude-opus-4-7",
            inp=1_000_000,
            out=0,
        ),
        _story_run(
            stage="verify",
            model="claude-sonnet-4-6",
            inp=1_000_000,
            out=0,
        ),
    )
    report = _build_report(runs)
    prices = {
        "opus": project.Pricing(
            input=15.0, output=75.0, cache_read=1.5, cache_write=18.75
        ),
        "sonnet": project.Pricing(
            input=3.0, output=15.0, cache_read=0.3, cache_write=3.75
        ),
    }

    result = ab_build.compute_cost(report, prices)

    assert result.grand_total[4] == 18.0  # 15 (opus) + 3 (sonnet)
    assert result.unpriced_models == ()


def test_compute_cost_wall_clock_per_stage() -> None:
    """Wall clock time is summed per stage."""
    runs = (
        _story_run(stage="shape", duration_s=30.0),
        _story_run(stage="shape", duration_s=45.0),
    )
    report = _build_report(runs)
    prices = _prices()

    result = ab_build.compute_cost(report, prices)

    shape_row = next(r for r in result.per_stage if r[0] == "shape")
    assert shape_row[6] == 75.0  # wall clock: 30 + 45 (index 6)


# ── collect_quality ──────────────────────────────────────────────


def test_collect_quality_counts_blocked_and_ac_states() -> None:
    """collect_quality counts blocked stories and AC pass/fail/waived states."""
    criteria = (
        _criterion("ac-01", passes=True),
        _criterion("ac-02", passes=True),
        _criterion("ac-03", passes=True),
        _criterion("ac-04", passes=False),
        acceptance.AcceptanceCriterion(
            id="ac-05", text="waived criterion", passes=False, waived=True
        ),
    )
    note = _issue_note(criteria)
    story_notes = (
        _story_note("completed"),
        _story_note("completed"),
        _story_note("in-progress"),
        _story_note("blocked"),
    )

    result = ab_build.collect_quality(note, story_notes)

    assert result == ab_build.QualityStats(
        total_stories=4,
        blocked_stories=1,
        ac_pass_count=3,
        ac_fail_count=1,
        ac_waived_count=1,
    )


def test_collect_quality_handles_none_issue_note() -> None:
    """collect_quality returns all-zero QualityStats when issue_note is None."""
    result = ab_build.collect_quality(None, ())

    assert result == ab_build.QualityStats(
        total_stories=0,
        blocked_stories=0,
        ac_pass_count=0,
        ac_fail_count=0,
        ac_waived_count=0,
    )


# ── build_comparison ─────────────────────────────────────────────


def test_build_comparison_produces_stage_grouped_rows_plus_totals() -> None:
    """build_comparison produces per-stage cost rows plus grand totals."""
    baseline_runs = (
        _story_run(stage="implement", inp=1000, out=500, duration_s=30.0),
        _story_run(stage=None, inp=200, out=100, duration_s=5.0),
    )
    candidate_runs = (
        _story_run(stage="implement", inp=800, out=400, duration_s=25.0),
    )
    prices = _prices()

    baseline = _build_artefacts("baseline", 89, baseline_runs)
    candidate = _build_artefacts("candidate", 90, candidate_runs)

    comp = ab_build.build_comparison(baseline, candidate, prices)

    assert comp.baseline_label == "baseline"
    assert comp.candidate_label == "candidate"
    assert comp.baseline_issue == 89
    assert comp.candidate_issue == 90

    metrics_by_stage = {}
    for row in comp.cost_rows:
        metrics_by_stage.setdefault(row.stage, []).append(row.metric)

    # implement stage rows present
    assert "implement" in metrics_by_stage
    impl_metrics = metrics_by_stage["implement"]
    assert "tokens_in" in impl_metrics
    assert "tokens_out" in impl_metrics
    assert "wall_clock_s" in impl_metrics
    assert "cost_usd" in impl_metrics

    # grand totals rows (stage=None, metric starting with "total_")
    total_rows = [r for r in comp.cost_rows if r.metric.startswith("total_")]
    assert len(total_rows) == 4
    total_metrics = {r.metric for r in total_rows}
    assert total_metrics == {
        "total_tokens_in",
        "total_tokens_out",
        "total_wall_clock_s",
        "total_cost_usd",
    }

    # delta = candidate - baseline
    impl_in_row = next(
        r
        for r in comp.cost_rows
        if r.stage == "implement" and r.metric == "tokens_in"
    )
    assert impl_in_row.delta == pytest.approx(
        impl_in_row.candidate - impl_in_row.baseline
    )


def test_build_comparison_empty_stories_on_both_sides() -> None:
    """Empty builds produce only grand-total cost rows (all zeros), quality still works."""
    baseline = _build_artefacts("baseline", 89, ())
    candidate = _build_artefacts("candidate", 90, ())
    prices = _prices()

    comp = ab_build.build_comparison(baseline, candidate, prices)

    # Only grand-total rows — no stage rows
    non_total_cost_rows = [
        r for r in comp.cost_rows if not r.metric.startswith("total_")
    ]
    assert non_total_cost_rows == []

    total_rows = [r for r in comp.cost_rows if r.metric.startswith("total_")]
    assert len(total_rows) == 4
    for row in total_rows:
        assert row.baseline == 0.0
        assert row.candidate == 0.0
        assert row.delta == 0.0


# ── render_markdown ──────────────────────────────────────────────


def test_render_markdown_emits_stage_subsections_in_canonical_order() -> None:
    """render_markdown groups cost by canonical stage order."""
    baseline_runs = (
        _story_run(stage="verify", inp=100, out=50, duration_s=10.0),
        _story_run(stage="shape", inp=200, out=80, duration_s=20.0),
        _story_run(stage="implement", inp=150, out=60, duration_s=15.0),
        _story_run(stage=None, inp=50, out=25, duration_s=5.0),
    )
    baseline = _build_artefacts("baseline-label", 89, baseline_runs)
    candidate = _build_artefacts("candidate-label", 90, ())
    prices = _prices()

    comp = ab_build.build_comparison(baseline, candidate, prices)
    output = ab_build.render_markdown(comp)

    # Verify canonical ordering: shape before implement before verify
    shape_pos = output.index("## Cost — shape")
    impl_pos = output.index("## Cost — implement")
    verify_pos = output.index("## Cost — verify")
    unattr_pos = output.index("## Cost — Unattributed")

    assert shape_pos < impl_pos < verify_pos < unattr_pos

    assert output == snapshot("""\
# A/B build comparison

- baseline: baseline-label
- candidate: candidate-label
- issues: 89 vs 90

## Cost — shape

| Metric | Baseline | Candidate | Δ |
|--------|----------|-----------|---|
| tokens_in | 200 | 0 | -200 |
| tokens_out | 80 | 0 | -80 |
| wall_clock_s | 20.0 | 0.0 | -20.0 |
| cost_usd | 0.0018 | 0.0000 | -0.0018 |

## Cost — implement

| Metric | Baseline | Candidate | Δ |
|--------|----------|-----------|---|
| tokens_in | 150 | 0 | -150 |
| tokens_out | 60 | 0 | -60 |
| wall_clock_s | 15.0 | 0.0 | -15.0 |
| cost_usd | 0.0014 | 0.0000 | -0.0014 |

## Cost — verify

| Metric | Baseline | Candidate | Δ |
|--------|----------|-----------|---|
| tokens_in | 100 | 0 | -100 |
| tokens_out | 50 | 0 | -50 |
| wall_clock_s | 10.0 | 0.0 | -10.0 |
| cost_usd | 0.0010 | 0.0000 | -0.0010 |

## Cost — Unattributed

| Metric | Baseline | Candidate | Δ |
|--------|----------|-----------|---|
| tokens_in | 50 | 0 | -50 |
| tokens_out | 25 | 0 | -25 |
| wall_clock_s | 5.0 | 0.0 | -5.0 |
| cost_usd | 0.0005 | 0.0000 | -0.0005 |

## Grand Totals

| Metric | Baseline | Candidate | Δ |
|--------|----------|-----------|---|
| total_tokens_in | 500 | 0 | -500 |
| total_tokens_out | 215 | 0 | -215 |
| total_wall_clock_s | 50.0 | 0.0 | -50.0 |
| total_cost_usd | 0.0047 | 0.0000 | -0.0047 |

## Quality

| Metric | Baseline | Candidate | Δ |
|--------|----------|-----------|---|
| total_stories | 0 | 0 | +0 |
| blocked_stories | 0 | 0 | +0 |
| ac_pass_count | 0 | 0 | +0 |
| ac_fail_count | 0 | 0 | +0 |
| ac_waived_count | 0 | 0 | +0 |
""")


def test_render_markdown_never_emits_sentinels() -> None:
    """render_markdown never contains sentinel placeholder strings (AC-03)."""
    baseline_runs = (
        _story_run(stage="implement", inp=0, out=0, duration_s=0.0),
    )
    baseline = _build_artefacts("zero-baseline", 89, baseline_runs)
    candidate = _build_artefacts("zero-candidate", 90, ())
    prices = _prices()

    comp = ab_build.build_comparison(baseline, candidate, prices)
    output = ab_build.render_markdown(comp)

    for sentinel in ("<fill>", "TBD", "pending", "<x>", "<y>"):
        assert sentinel not in output, f"Sentinel {sentinel!r} found in output"


def test_render_markdown_surfaces_unpriced_warning() -> None:
    """render_markdown includes a warning line for unpriced models."""
    run = _story_run(
        stage="implement", model="ancient-model", inp=1000, out=500
    )
    baseline = _build_artefacts("baseline", 89, (run,))
    candidate = _build_artefacts("candidate", 90, ())
    prices = _prices()  # no "ancient-model"

    comp = ab_build.build_comparison(baseline, candidate, prices)
    output = ab_build.render_markdown(comp)

    assert "ancient-model" in output
    assert "unpriced" in output.lower()


def test_render_markdown_full_snapshot() -> None:
    """Full render snapshot for a handcrafted Comparison."""
    criteria = (
        _criterion("ac-01", passes=True),
        _criterion("ac-02", passes=False),
    )
    note = _issue_note(criteria)
    story_notes = (
        _story_note("completed"),
        _story_note("blocked"),
    )

    baseline_runs = (
        _story_run(stage="shape", inp=500, out=200, duration_s=20.0),
        _story_run(stage="implement", inp=2000, out=800, duration_s=60.0),
    )
    candidate_runs = (
        _story_run(stage="shape", inp=400, out=180, duration_s=18.0),
        _story_run(stage="implement", inp=1800, out=720, duration_s=55.0),
    )
    baseline = _build_artefacts(
        "budget-preset", 89, baseline_runs, note, story_notes
    )
    candidate = _build_artefacts(
        "quality-preset", 90, candidate_runs, note, story_notes
    )
    prices = _prices()

    comp = ab_build.build_comparison(baseline, candidate, prices)
    output = ab_build.render_markdown(comp)

    assert output == snapshot("""\
# A/B build comparison

- baseline: budget-preset
- candidate: quality-preset
- issues: 89 vs 90

## Cost — shape

| Metric | Baseline | Candidate | Δ |
|--------|----------|-----------|---|
| tokens_in | 500 | 400 | -100 |
| tokens_out | 200 | 180 | -20 |
| wall_clock_s | 20.0 | 18.0 | -2.0 |
| cost_usd | 0.0045 | 0.0039 | -0.0006 |

## Cost — implement

| Metric | Baseline | Candidate | Δ |
|--------|----------|-----------|---|
| tokens_in | 2000 | 1800 | -200 |
| tokens_out | 800 | 720 | -80 |
| wall_clock_s | 60.0 | 55.0 | -5.0 |
| cost_usd | 0.0180 | 0.0162 | -0.0018 |

## Grand Totals

| Metric | Baseline | Candidate | Δ |
|--------|----------|-----------|---|
| total_tokens_in | 2500 | 2200 | -300 |
| total_tokens_out | 1000 | 900 | -100 |
| total_wall_clock_s | 80.0 | 73.0 | -7.0 |
| total_cost_usd | 0.0225 | 0.0201 | -0.0024 |

## Quality

| Metric | Baseline | Candidate | Δ |
|--------|----------|-----------|---|
| total_stories | 2 | 2 | +0 |
| blocked_stories | 1 | 1 | +0 |
| ac_pass_count | 1 | 1 | +0 |
| ac_fail_count | 1 | 1 | +0 |
| ac_waived_count | 0 | 0 | +0 |
""")
