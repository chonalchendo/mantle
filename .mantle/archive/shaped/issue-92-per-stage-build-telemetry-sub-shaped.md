---
issue: 92
title: 'Per-stage build telemetry: sub-agent JSONL read path + universal stage-begin
  primitive'
approaches:
- A — Add sub-agent read path, keep old parent-sidechain fallback
- B — Replace the parent-sidechain path with sub-agent-file clustering
- C — Full begin/end stage markers in build.md
- D (revised) — Sub-agent read path + universal single-event stage-begin (chosen)
chosen_approach: D (revised) — Sub-agent read path + universal single-event stage-begin
appetite: medium batch
open_questions:
- general-purpose agent-type disambiguation if a non-build caller appears — defer
  until it does
- cross-session aggregation order for audit-tokens and issue 89's A/B harness — flag
  for 89, not in 92's scope
- stages-<session>.jsonl rotation — punted; delete old by mtime if they accumulate
- template skip list final cut — implementer decides at story time from proposed skip
  set
- issue-92.md body needs rewriting to reflect D-revised scope + .mantle/telemetry/
  storage before plan-stories runs
author: 110059232+chonalchendo@users.noreply.github.com
created: '2026-04-24'
updated: '2026-04-24'
updated_by: 110059232+chonalchendo@users.noreply.github.com
tags:
- type/shaped
- phase/shaping
---

## Context

Issue 92 was originally written to fix `telemetry.find_session_file` / `read_session` reading the wrong location — sub-agent transcripts live at `<parent_session>/subagents/agent-*.jsonl`, not as sidechain turns in the parent JSONL. Diagnosis during issue 89's shaping confirmed: build-90's session JSONL has 188 `isSidechain: false` turns and zero sidechain clusters; its 5 sub-agent spawns (3× story-implementer, 1× refactorer, 1× general-purpose) live in separate files. `telemetry.group_stories` was clustering a set that's always empty for recent builds — the `stories: []` in build reports is the observable symptom.

The user's additional constraint surfaced during shaping: stage attribution must work for every LLM-invoking Mantle command, **not only inside `/mantle:build`**. A standalone `/mantle:shape-issue` or `/mantle:verify` invocation should also be attributable. This collapses "build stages" and "standalone commands" into one concept: a stage is any named Mantle command that does LLM reasoning, inside or outside the build pipeline.

## Approaches evaluated

### Approach A — Add sub-agent read path, keep old parent-sidechain fallback

Mechanical read of issue 92's original "What to build". Adds `find_subagent_files` / `read_subagent` / `read_meta` alongside the existing parser; widens `StoryRun` with `stage`; attributes stage from `agentType` via `story-implementer→implement`, `refactorer→simplify`, `general-purpose→verify`. Old clustering kept as fallback.

- Appetite: small batch (1-2 days).
- Pros: strictly the issue-92 body as written.
- Cons: covers 3 of 5 in-build stages only (shape + plan_stories run inline in parent session and are invisible). Standalone commands uncovered. Old fallback is likely dead code.

### Approach B — Replace the parent-sidechain path

Same as A, but delete the old clustering. Premise: recent builds have no parent-sidechain turns, so the old code is unreachable. Single code path; smaller module.

- Appetite: small batch (1-2 days).
- Pros: cleaner module; no special-general mixture.
- Cons: same 3-of-5 coverage as A; same no-coverage for standalone commands.

### Approach C — Full begin/end stage markers emitted from orchestrator

`mantle stage-begin <name>` + `mantle stage-end <name>` pairs emitted around every stage in `build.md`. Parser slices parent turns by windows; sub-agent files attribute independently.

- Appetite: medium batch (3-5 days).
- Pros: covers all 7 build stages including inline shape/plan_stories.
- Cons: begin/end pair creates orphan-end bookkeeping on crashes/resumes; still doesn't cover standalone commands (markers only fire when `build.md` runs).

### Approach D (revised) — Sub-agent read path + universal single-event `stage-begin` (CHOSEN)

Combines B's code path with a universal stage-marking primitive applied at the entry of every LLM-invoking Mantle command template — not just inside the build orchestrator. One `mantle stage-begin <name>` line at the top of each relevant `/mantle:*` template appends a `{stage, at}` record to `.mantle/telemetry/stages-<session_id>.jsonl`. Next mark is the implicit close of the previous window; session end closes the final window.

Parser reads the parent JSONL (for inline turns), the session's `stages-<session_id>.jsonl` (for windows over the parent), and all sub-agent JSONLs (with `agentType` → stage attribution via meta sidecars). Returns a single chronological tuple of `StoryRun` records with populated `stage`.

- Appetite: medium batch (3-5 days).
- Pros:
  - Works inside and outside the build pipeline — standalone `/mantle:verify` or `/mantle:shape-issue` runs get attributed for free.
  - Single-event markers have no orphan-end problem (next mark terminates the prior stage).
  - One uniform primitive across 12-15 templates; each edit is one line.
  - Parity harness (issue 90) catches template drift automatically.
  - Removes dead code (old parent-sidechain clustering) in the same pass.
  - Per-session file (named by session id) eliminates cross-worktree write races and makes rotation trivial (delete by mtime).
- Cons:
  - Template edit volume is the bulk of the work; parity snapshots refresh for every touched template.
  - `general-purpose` agent type is currently always "verify" in build context; a future caller could surprise the mapping.

## Chosen approach: D (revised)

Sub-agent JSONL read path (from B) + universal `mantle stage-begin <name>` primitive emitted at the entry of every LLM-invoking Mantle command template. Stage marks are stored per-session at `.mantle/telemetry/stages-<session_id>.jsonl` — co-located with the existing `baseline-*.md`/`.json` telemetry artefacts. Parser reads the per-session file at build-finish time (and by `mantle audit-tokens` / issue 89's A/B harness later) to attribute inline parent-session turns to the correct stage.

The user explicitly confirmed this scope: instrument **every LLM-invoking template in one pass** rather than deferring standalone commands to a follow-up. The template-edit cost is linear and each edit is one line; one pass keeps the parity-harness diff churn confined to a single build.

### Why not A or B

They solve the read path but leave shape, plan_stories, and every standalone command unattributed. Issue 89's AC-02 ("per-stage cost/time") is only partially satisfied, and the user's "consistently accurate" requirement rules out partial coverage.

### Why not C

Begin/end pairs add orphan-end handling for crashes/resumes. Single-event markers ("the next begin is the previous end") are strictly simpler and lose no correctness since we care about stage windows, not stage-failure detection.

## Appetite

Medium batch (3-5 days).

## Code design

### Data model

**On disk.** Append-only, newline-delimited JSON at `.mantle/telemetry/stages-<session_id>.jsonl`, one file per Claude Code session. `session_id` lives in the filename; each record carries only `{stage, at}`:

```jsonl
{"stage": "shape-issue", "at": "2026-04-24T13:20:00.000Z"}
{"stage": "plan-stories", "at": "2026-04-24T13:35:11.234Z"}
{"stage": "build", "at": "2026-04-24T13:40:00.000Z"}
{"stage": "shape", "at": "2026-04-24T13:40:05.000Z"}
{"stage": "plan_stories", "at": "2026-04-24T13:42:30.000Z"}
```

Telemetry folder layout after this issue:

```
.mantle/telemetry/
├── baseline-2026-04-21.md           # existing: human-readable A/B report
├── baseline-2026-04-21.json         # existing: machine-readable companion
└── stages-<session-id>.jsonl        # NEW: append-only stage marks per session
```

**In Python** (`core/stages.py`):

```python
class StageMark(pydantic.BaseModel, frozen=True):
    """One stage-begin event parsed from stages-<session_id>.jsonl."""
    stage: str
    at: datetime

class StageWindow(pydantic.BaseModel, frozen=True):
    """Half-open [start, end) window attributed to a stage."""
    stage: str
    start: datetime
    end: datetime    # next mark's `at`, or session end for the last mark
```

**`core/telemetry.py` extensions:**

```python
class SubagentMeta(pydantic.BaseModel, frozen=True):
    model_config = ConfigDict(extra="ignore")  # Claude Code owns this schema
    agent_type: str = Field(alias="agentType")

class StoryRun(pydantic.BaseModel, frozen=True):
    # existing fields unchanged ...
    stage: str | None = None   # NEW — "implement" | "simplify" | "verify" | None
```

Two models because `StageMark` is the on-disk event (author-side) and `StageWindow` is the parser-side interval (consumer-side). Keeping them separate stabilises the on-disk format while the consumer interface can evolve.

### Strategy

Four cohesive additions, ordered by dependency.

**1. New: `src/mantle/core/stages.py`** — the marker primitive.

- Models `StageMark` and `StageWindow` as above.
- `record_stage(stage: str, project_dir: Path | None = None) -> None` — resolves session id via `telemetry.current_session_id`; appends one JSONL line to `<project_dir>/.mantle/telemetry/stages-<session_id>.jsonl` (creating the directory if absent). Silent no-op when no session id is resolvable (matches `build-start` behaviour).
- `read_stages(session_id: str, project_dir: Path | None = None) -> tuple[StageMark, ...]` — parses that session's jsonl in chronological order; malformed lines silently skipped (same policy as `telemetry.read_session`); returns `()` when the file is absent.
- `windows_for_session(marks: tuple[StageMark, ...], session_end: datetime) -> tuple[StageWindow, ...]` — pure function; sorts by `at`, produces half-open windows closing either at the next mark or at `session_end`.

`core/stages.py` depends only on `core.telemetry` (for `current_session_id`) + stdlib. No cross-layer imports.

**2. Extend: `src/mantle/core/telemetry.py`** — the read path.

- `SubagentMeta` and `StoryRun.stage` additions as above.
- `find_subagent_files(parent_session_id, projects_root=None) -> tuple[Path, ...]` — glob `<parent>/subagents/agent-*.jsonl`; order by first-turn timestamp.
- `read_subagent(jsonl_path) -> tuple[Turn, ...]` — identical to `read_session` (sub-agent files have the same assistant-turn shape with `isSidechain: true`). Reuse `_parse_assistant_line`.
- `read_meta(jsonl_path) -> SubagentMeta | None` — parse sibling `agent-*.meta.json`. Returns None on absence or malformed JSON; callers degrade to `stage=None`.
- `_AGENT_TYPE_TO_STAGE: Mapping[str, str]` — `{story-implementer: implement, refactorer: simplify, general-purpose: verify}`. Unknown agent types map to `None`.
- `group_stories(parent_turns, subagent_paths=(), stage_windows=()) -> tuple[StoryRun, ...]` — rewrites the old clustering. Produces one `StoryRun` per sub-agent file (stage from meta) plus one per `StageWindow` that overlaps the parent session (aggregating parent turns inside the window). Returns runs sorted by `started`.
- `render_report` groups stories by `stage` (with an "Unattributed" bucket for `stage=None`).
- Deletions: `_aggregate_cluster`'s sidechain-cluster logic, `Marker`, `MarkerWindowWarning`, `_attach_story_ids`, `_derive_mtime_markers` (in `cli/builds.py`). These all served the parent-sidechain clustering which is unused against current Claude Code builds.

**3. New CLI command: `mantle stage-begin <name>`** in `src/mantle/cli/main.py` under `GROUPS["impl"]`.

```python
@app.command(name="stage-begin", group=GROUPS["impl"])
def stage_begin_command(name: str) -> None:
    """Mark the start of a named stage in the current session."""
    stages.record_stage(name)
```

No flags. Single positional argument. Graceful no-op when no session id is resolvable.

**4. Template edits across `claude/commands/mantle/`**

Add `mantle stage-begin <stage-name>` as the first shell call in every LLM-invoking `.md` template. Stage name matches the `cost-policy.md` key where applicable (`shape`, `plan_stories`, `implement`, `simplify`, `verify`, `review`, `retrospective`), matches the command slug otherwise (`build`, `challenge`, `design-product`, `design-system`, `revise-product`, `revise-system`, `brainstorm`, `research`, `scout`, `adopt`, `refactor`, `plan-issues`, `idea`, `patterns`, `distill`, `fix`).

Skip: `help.md`, `resume.md.j2`, `status.md.j2`, `add-issue.md`, `add-skill.md`, `bug.md`, `inbox.md`, `query.md` — these are wiring or short non-reasoning commands. Implementer may refine the skip list at story time.

`build.md` additionally emits `mantle stage-begin shape` at the start of Step 4 and `mantle stage-begin plan_stories` at the start of Step 5, because those stages run inline inside the orchestrator rather than via nested slash-command invocations.

**5. `build-finish` wiring** in `src/mantle/cli/builds.py`

`run_build_finish` now:
1. Reads parent session JSONL (unchanged).
2. Reads stage marks via `stages.read_stages(session_id)`; converts to windows via `stages.windows_for_session(marks, report.finished)`.
3. Resolves sub-agent JSONL paths via `telemetry.find_subagent_files(session_id)`.
4. Calls `telemetry.group_stories(parent_turns, subagent_paths, stage_windows)`.
5. Renders.

Old `_derive_mtime_markers` is deleted.

### Acceptance criteria (to refresh on the issue body)

- ac-01: `mantle stage-begin <name>` appends a well-formed JSONL `StageMark` to `.mantle/telemetry/stages-<session_id>.jsonl` when a Claude Code session id is resolvable; no-ops silently otherwise. Creates `.mantle/telemetry/` if absent.
- ac-02: `telemetry.group_stories()` returns one `StoryRun` per sub-agent JSONL under `<parent>/subagents/`, with `stage` populated from `agentType` via the mapping `story-implementer→implement`, `refactorer→simplify`, `general-purpose→verify`; unknown types yield `stage=None`.
- ac-03: Parent-session inline turns are attributed to a stage when a `StageWindow` overlaps their timestamp; turns outside any window get `stage=None` (surfaced as "Unattributed" in the rendered report).
- ac-04: A synthetic roundtrip fixture — parent JSONL + `subagents/` dir + `stages-<session_id>.jsonl` — renders a build report whose `stories:` frontmatter contains stage-grouped rows per `inline_snapshot` capture.
- ac-05: Re-parsing build-90's real session directory (copied into a test fixture) produces `implement` ×3 + `simplify` ×1 + `verify` ×1; inline stages show `stage=None` because build-90 predates marker emission.
- ac-06: Every LLM-invoking `.md` template in `claude/commands/mantle/` begins with `mantle stage-begin <name>`. Parity harness (`tests/parity/`) snapshots refreshed for all affected integrated commands.
- ac-07: `BuildReport` stays backward-compatible — pre-existing `.mantle/builds/build-NN-*.md` files load without error; `stage=None` renders as "Unattributed".
- ac-08: `just check` passes — ruff + ty + pytest, import-linter contracts unchanged.

### Fits architecture by

- **Core never imports CLI.** `core/stages.py` depends only on `core.telemetry` and stdlib. `core/telemetry.py` unchanged in dependency footprint. Import-linter contracts unchanged.
- **Deep-module posture** (`software-design-principles`). `core/telemetry.py` absorbs one more clustering strategy into its existing narrow public interface. `core/stages.py` is a small, cohesive module with three functions and two models — not a "Stager" class hierarchy.
- **Information hiding.** The knowledge that "sub-agent files are separate JSONLs" and "stage windows come from a per-session sidecar" lives only in `core/telemetry.py` + `core/stages.py`. Callers see `StoryRun.stage`; they never learn where the attribution came from.
- **Pydantic conventions.** `frozen=True` on all new models; `extra="ignore"` on `SubagentMeta` since Claude Code owns that schema.
- **Parity harness integration.** Template edits land as expected snapshot diffs; reviewer accepts via `--inline-snapshot=review`. This is the mechanism issue 90 built the harness for.
- **Storage pattern consistency.** `.mantle/telemetry/stages-<session_id>.jsonl` co-locates with the existing `baseline-*.md/.json` telemetry artefacts. One file per session mirrors the Claude Code projects-dir pattern (`<slug>/<session_id>.jsonl`) and eliminates cross-worktree write races by construction.

### Does not

- Does not emit `stage-end` — single-event marks only; next `stage-begin` implicitly closes the previous window.
- Does not persist stage state anywhere other than `.mantle/telemetry/stages-<session_id>.jsonl`. No DB, no index, no compaction.
- Does not retroactively attribute historical builds. Pre-existing build files keep `stage=None` on inline turns.
- Does not disambiguate `general-purpose` beyond the build-context mapping. If a future caller spawns `general-purpose` for non-verify work, `StoryRun.stage` will read `verify` incorrectly — acceptable while `build.md` is the only caller.
- Does not instrument plumbing CLI calls (`mantle update-story-status`, `mantle save-shaped-issue`, etc.).
- Does not rotate or compact `stages-*.jsonl` files. Old sessions' files can be deleted manually if needed; mtime sort works.
- Does not add price application to `StoryRun` — that belongs to `core/ab_build.py` (issue 89 scope).
- Does not instrument `help.md`, `resume.md.j2`, `status.md.j2`, or short wiring commands.
- Does not change `StoryRun.story_id`. `story_id` stays for per-story granularity inside `implement`; `stage` is the coarser axis.
- Does not re-home `Marker` / `MarkerWindowWarning` — they are deleted along with the old mtime-based marker derivation.
- Does not emit telemetry from non-LLM commands. Stage-begin is called explicitly at template entry; there is no implicit per-CLI-subcommand log.
- Does not absorb `cli/builds.py:_derive_mtime_markers`'s responsibility. That helper is deleted — the generalised stage primitive supersedes it.
- Does not validate the stage name at CLI entry beyond "non-empty". Typos in template edits are caught at snapshot-review time via the parity harness.

## Open questions

1. **`general-purpose` disambiguation for non-build callers.** Defer. Add a `context=` argument to `stage-begin` only if a second caller of `general-purpose` surfaces.
2. **Cross-session aggregation order for `audit-tokens` and 89's A/B harness.** Per-session files mean aggregators glob `stages-*.jsonl` and decide how to order sessions. Not in 92's scope but worth flagging for 89 / audit-tokens.
3. **`stages-*.jsonl` rotation.** Punted. Old session files can be deleted by mtime if they accumulate.
4. **Skip list for templates.** Implementer exercises judgment at story time. Proposed skip: `help.md`, `resume.md.j2`, `status.md.j2`, `add-issue.md`, `add-skill.md`, `bug.md`, `inbox.md`, `query.md`.
5. **Backward compatibility of old `Marker` / `MarkerWindowWarning` exports.** Deletion is safe — grep confirms `_derive_mtime_markers` is the only caller. If any external prompt or downstream tool imports these symbols, the story implementing this change must catch it.
6. **Issue 92's original body.** Needs to be rewritten to reflect the D-revised scope (marker primitive + universal template instrumentation + per-session storage). Plan to refresh issue-92.md before `/mantle:plan-stories`.