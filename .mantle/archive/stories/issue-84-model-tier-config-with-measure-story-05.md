---
issue: 84
title: Introduce .mantle/telemetry/ and hand-run baseline measurement
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a Mantle user considering a cheaper tier, I want a measured before/after dollar + time comparison, so the trade-off against Opus is evidence-backed not taste-driven.

## Depends On

Stories 1–4 complete (need a working `balanced` preset to run the "after" measurement).

## Approach

Split into a small code change (introduce `.mantle/telemetry/` as a convention via `SUBDIRS` so future telemetry lands in a known place) plus a hand-authored baseline report driven by two real `/mantle:build` runs parsed through the existing `core/telemetry.py`. Dollar cost comes from published Claude per-token prices plugged into a per-model table inside the baseline document itself — no new code pathway for pricing. This is consistent with the shaped doc's "no new CLI" constraint.

## Implementation

### src/mantle/core/project.py (modify — one-line addition)

Add `"telemetry"` to the existing `SUBDIRS` tuple so `init_project` creates the folder alongside `bugs/`, `learnings/`, etc. Keep alphabetical ordering (insert between `stories` and whatever comes after — check current ordering during implementation; the existing tuple ends with `"stories"`, so append).

```python
SUBDIRS: tuple[str, ...] = (
    "bugs",
    "challenges",
    "decisions",
    "distillations",
    "inbox",
    "issues",
    "learnings",
    "research",
    "sessions",
    "shaped",
    "stories",
    "telemetry",
)
```

Also: ensure the current project's `.mantle/telemetry/` directory is created at implementation time (won't be picked up by `init_project` in this repo because init already ran) — a one-time `mkdir -p .mantle/telemetry` in the implementation session.

### .mantle/telemetry/baseline-2026-04-21.md (new file — hand-authored, real numbers)

Author this file during the implementation session. Procedure:

1. Pick a small, representative issue for the measurement — a 1–2 story issue so total wall-clock and cost stay modest. Good candidate: any `planned` issue with small slice that hasn't been built yet, OR re-run an already-built issue by resetting its status.
2. **Before-run (Opus default)**: temporarily set `models.overrides` on every stage to `opus`, or comment out the `models:` block entirely and ensure the fallback preset yields opus-on-implement (it doesn't under the template defaults — for the "before" baseline we need a `quality`-equivalent config that matches the current pre-issue-84 behaviour; use `preset: quality` with a manual override bumping `simplify`/`verify`/`review`/`retrospective` to opus).
3. Run `/mantle:build <chosen issue>`. Record the Claude Code session id.
4. Revert the config change; run the same issue (or a sibling issue of equivalent shape) with `preset: balanced`. Record the second session id.
5. For each session, parse the JSONL via `core.telemetry.read_session` + `group_stories` + `summarise`. Extract per-stage durations and token counts. Compute dollar cost by multiplying input/output/cache token counts by the per-model prices documented in the report itself.
6. Write the comparison into `.mantle/telemetry/baseline-2026-04-21.md` using the template below.

Report template (skeleton — fill in real numbers during implementation):

```markdown
---
date: 2026-04-21
issue_measured: <issue number>
session_before: <claude code session uuid for opus run>
session_after: <claude code session uuid for balanced run>
tags:
  - type/telemetry
---

## Method

Two `/mantle:build <NN>` runs on the same issue (or equivalent issues)
under two configurations:

- **Before** — `preset: quality` with every stage forced to opus,
  approximating the pre-issue-84 default behaviour.
- **After** — `preset: balanced` (no overrides).

Session JSONLs parsed via `mantle.core.telemetry`. Dollar cost computed
from the published Claude prices in the pricing table below, multiplied
by the token counts reported by the telemetry module.

## Prices used

| Model | Input $/MT | Output $/MT | Cache read $/MT | Cache write $/MT |
|-------|-----------:|------------:|----------------:|-----------------:|
| opus  | <fill>     | <fill>      | <fill>          | <fill>           |
| sonnet| <fill>     | <fill>      | <fill>          | <fill>           |
| haiku | <fill>     | <fill>      | <fill>          | <fill>           |

## Results

| Stage | Before model | After model | Before $ | After $ | Before seconds | After seconds |
|-------|--------------|-------------|---------:|--------:|---------------:|--------------:|
| shape          | opus   | opus   | ... | ... | ... | ... |
| plan_stories   | opus   | sonnet | ... | ... | ... | ... |
| implement      | opus   | sonnet | ... | ... | ... | ... |
| simplify       | opus   | sonnet | ... | ... | ... | ... |
| verify         | opus   | sonnet | ... | ... | ... | ... |
| review         | opus   | haiku  | ... | ... | ... | ... |
| retrospective  | opus   | haiku  | ... | ... | ... | ... |
| **Total**      |        |        | **<x>** | **<y>** | **<a>** | **<b>** |

## Interpretation

<1–2 paragraphs: what the dollar/time deltas say about the balanced
preset. Any stage where the after run was *slower* than the before
(expected on stages where haiku needs more retries) should be called
out explicitly.>
```

#### Design decisions

- **telemetry in SUBDIRS.** Makes the folder exist for new projects without requiring a `mantle telemetry init`-style command. For this project (already initialised), the implementation session creates the folder manually.
- **Baseline as hand-authored markdown, not generated output.** The shaped doc explicitly says "no new CLI". Dollar-cost arithmetic is trivial but requires a pricing table the user curates — putting prices into code would drift. Keeping the full report in markdown means the next baseline (for a future preset tweak) follows the same authoring pattern.
- **Before-run uses "all opus", not pre-issue-84 master.** The "before" baseline needs to be reproducible after the code lands. "All opus" via `preset: quality` with overrides is the closest faithful reproduction of the pre-84 default.
- **One baseline file, not a time-series.** `baseline-<date>.md` accumulates as files over time; no rollup or aggregation is built in this story. Future retrospectives can read the folder directly if needed.
- **No template file shipped under vault-templates/.** The baseline is a one-off report, not something users will re-run from a template. Keeping the template inline in this story's notes (for the implementation agent to fill in) avoids accreting boilerplate.

## Tests

### tests/core/test_project.py (modify)

Extend `TestInitProject` / `TestTemplateConstants`:

- **test_creates_telemetry_subdir**: After `init_project(tmp_path, "test-project")`, `(tmp_path / ".mantle" / "telemetry").is_dir()` is True.
- **test_telemetry_in_subdirs**: Add `assert "telemetry" in SUBDIRS` under `TestTemplateConstants.test_subdirs_expected`.

### Manual verification for the baseline report

No automated test for `baseline-2026-04-21.md` itself — it's a human-authored artefact. Verification at `/mantle:verify` time for this story confirms:

1. `.mantle/telemetry/` exists.
2. `.mantle/telemetry/baseline-<date>.md` exists with non-placeholder numbers (total before-$ > 0, total after-$ > 0, `session_before` and `session_after` frontmatter keys are valid UUIDs).

Flag for the user: the measurement requires two real LLM runs; expect wall-clock minutes and a small dollar spend. This is the one ac-04 step that cannot be fully automated in the implementation session — the agent can set up the telemetry folder, the pricing table, and the empty report skeleton, but the user (or the implementing agent running the pipeline) must execute the two builds and fill in the numbers.
