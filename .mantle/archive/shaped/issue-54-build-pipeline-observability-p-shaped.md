---
issue: 54
title: Build pipeline observability — per-story model and performance telemetry
approaches:
- 'A: LLM self-report'
- 'B: Post-hoc JSONL parse'
- 'C: Full OpenTelemetry instrumentation'
chosen_approach: 'B: Post-hoc JSONL parse'
appetite: small batch
open_questions:
- Story-to-sidechain correlation — timestamp window vs captured turn uuid?
- CLAUDE project JSONL path on CI runners?
author: 110059232+chonalchendo@users.noreply.github.com
created: '2026-04-12'
updated: '2026-04-12'
updated_by: 110059232+chonalchendo@users.noreply.github.com
tags:
- type/shaped
- phase/shaping
---

## Approaches

### Approach A — LLM self-report
Story-implementer agents self-report model/tokens/duration in a final summary block; orchestrator extracts via regex.
- **Appetite:** small batch (~1 day)
- **Tradeoffs:** simple wiring; but LLM-reported stats are fragile, easy to omit, and duplicate data that Claude Code already records.
- **Rabbit holes:** agents forgetting the footer; regex brittleness; no second-attempt coverage on retries.
- **No-gos:** no token-level truth, no cache hit visibility.

### Approach B — Post-hoc JSONL parse (chosen)
Parse Claude Code's existing session JSONL (`~/.claude/projects/<slug>/<uuid>.jsonl`) after the build completes. Each assistant turn already carries `message.model`, full `usage` token breakdown, `timestamp`, and `isSidechain` flag. Group sidechain clusters by parent chain → one story. Grounded by research doc `.mantle/research/issue-54-build-observability.md`.
- **Appetite:** small batch (~1 day)
- **Tradeoffs:** zero LLM-side friction, accurate native data, forward-compatible with Anthropic issue #22625 schema. Cost: reading `~/.claude/projects/` from outside the repo.
- **Rabbit holes:** story ↔ sidechain correlation is the one non-trivial design call; Claude Code JSONL schema could drift.
- **No-gos:** no UI, no historical aggregation across builds, no routing changes.
- **Side-effect scan:** two new CLI calls added to `implement.md` (`mantle build-start` at Step 2 end, `mantle build-finish` at Step 6 start). Neither mutates story/issue state; both write to new `.mantle/builds/` directory. No ordering dependencies with existing calls.

### Approach C — Full OpenTelemetry-style instrumentation
Wrap every agent spawn with OTel spans, export to a collector.
- **Appetite:** medium batch (~3-5 days)
- **Tradeoffs:** future-proof, but orders of magnitude over-engineered for AC requirements; requires collector infra.
- **No-gos:** overkill for \"no routing changes — measurement only\".

## Comparison

|  | A: LLM self-report | B: JSONL parse (chosen) | C: OpenTelemetry |
|---|---|---|---|
| Appetite | ~1 day | ~1 day | 3-5 days |
| Accuracy | Medium | High (native) | High |
| Key risk | Agent forgets footer | JSONL schema drift | Over-engineering |
| Complexity | Low | Low | High |

## Chosen approach — rationale

B is the smallest approach that satisfies all ACs. Research confirmed that JSONL transcripts already contain everything the AC requires (model, tokens, timestamps, sidechain flag). Self-reporting (A) would duplicate truth; OTel (C) is disproportionate. B keeps implementation additive and reversible — if the schema drifts or native per-subagent metrics ship (Anthropic issue #22625), the parser swaps out without changing the report format.

## Code design

### Strategy

Three additive components:

1. **`src/mantle/core/telemetry.py`** — pure parser (no CLI, no mutation beyond reading JSONL). Key functions:
   - `read_session(session_id: str) -> list[Turn]` — parse JSONL for a session.
   - `group_stories(turns, story_markers) -> list[StoryRun]` — cluster sidechain turns by parent chain, align with `mantle update-story-status --in-progress` timestamps supplied as markers.
   - `summarise(story_runs) -> BuildReport` — aggregate per-story model/tokens/duration.
   - Types are frozen pydantic models: `Turn`, `Usage`, `StoryRun`, `BuildReport` — schema mirrors Anthropic issue #22625 for forward compatibility.

2. **`src/mantle/cli/builds.py`** — two cyclopts commands:
   - `mantle build-start --issue N` — captures current session id + start timestamp, writes stub to `.mantle/builds/build-{NN}-{YYYYMMDD-HHMM}.md`.
   - `mantle build-finish --issue N` — re-opens the stub, parses JSONL via `core.telemetry`, writes frontmatter + rendered summary table.

3. **`claude/commands/mantle/implement.md`** — add two CLI calls:
   - After Step 2 confirms issue: `mantle build-start --issue {NN}`
   - At Step 6 start (after all stories done): `mantle build-finish --issue {NN}`

### Build report format

File: `.mantle/builds/build-{NN}-{YYYYMMDD-HHMM}.md`

```yaml
---
issue: 54
started: 2026-04-12T14:02:11Z
finished: 2026-04-12T14:37:48Z
session_id: 0b112a41-...
stories:
  - id: 1
    model: claude-opus-4-6
    attempts:
      - {result: pass, duration_s: 412, input_tokens: 18240, output_tokens: 3120, cache_read: 94210}
    final: completed
---
## Summary
N stories · M first-pass · K retries · total wall: Xm · routing: opus/sonnet split
```

### Fits architecture by

- `core/telemetry.py` depends only on `core/` peers (session helpers) — respects CLAUDE.md rule: `core/` never imports from `cli/`.
- `cli/builds.py` is the thin wrapper the prompt already uses (same pattern as `cli/storage.py`, `cli/session.py`).
- Storage lives under `.mantle/` — consistent with the rest of project state.
- JSONL discovery reuses the existing session-directory resolution pattern.

### Does not

- Does not change routing logic (AC: measurement only).
- Does not add a cross-build aggregation view (out of scope; separate issue if ever wanted).
- Does not instrument non-implementation commands (shape, plan-stories, verify) — scope is build pipeline observability of story implementation.
- Does not attempt per-tool-call breakdown — per-agent granularity is sufficient for the stated AC.
- Does not modify the story-implementer prompt to self-report stats.
- Does not persist telemetry in story/issue frontmatter — separate build files keep concerns isolated.
- Does not backfill reports for past builds.

## Open questions

- Story ↔ sidechain correlation: timestamp window on `mantle update-story-status --in-progress` is the recommended cheapest approach. If it proves flaky (e.g., when retries cause re-spawns), fall back to recording the spawning turn's uuid via an orchestrator-side marker.
- JSONL location on non-macOS runners (CI): path resolution may need `$CLAUDE_PROJECT_DIR` environment lookup — to be confirmed during implementation.

## References

- `.mantle/research/issue-54-build-observability.md` — implementation research with JSONL field evidence and shaping implications.
- `.mantle/brainstorms/2026-04-11-ab-model-effort-routing.md` — origin context.