---
title: 'Per-stage build telemetry: sub-agent JSONL read path + universal stage-begin
  primitive'
status: approved
slice:
- core
- cli
- claude-code
- tests
story_count: 5
verification: null
blocked_by: []
skills_required:
- Design Review
- Designing Architecture
- Python 3.14
- Python Project Conventions
- Python package structure
- Software Design Principles
- dirty-equals
- import-linter
- inline-snapshot
- omegaconf
- pydantic-discriminated-unions
- pydantic-project-conventions
- python-314
tags:
- type/issue
- status/approved
acceptance_criteria:
- id: ac-01
  text: '`mantle stage-begin <name>` appends a well-formed JSONL `StageMark` to `.mantle/telemetry/stages-<session_id>.jsonl`
    when a Claude Code session id is resolvable; no-ops silently otherwise. Creates
    `.mantle/telemetry/` if absent.'
  passes: true
  waived: false
  waiver_reason: null
- id: ac-02
  text: '`telemetry.group_stories()` returns one `StoryRun` per sub-agent JSONL under
    `<parent>/subagents/`, with `stage` populated from `agentType` via `story-implementer→implement`,
    `refactorer→simplify`, `general-purpose→verify`; unknown types yield `stage=None`.'
  passes: true
  waived: false
  waiver_reason: null
- id: ac-03
  text: Parent-session inline turns are attributed to a stage when a `StageWindow`
    overlaps their timestamp; turns outside any window get `stage=None` (rendered
    as "Unattributed").
  passes: true
  waived: false
  waiver_reason: null
- id: ac-04
  text: Synthetic roundtrip fixture (parent JSONL + `subagents/` dir + `stages-<session_id>.jsonl`)
    renders a build report whose `stories:` frontmatter contains stage-grouped rows
    per `inline_snapshot` capture.
  passes: true
  waived: false
  waiver_reason: null
- id: ac-05
  text: Re-parsing build-90's real session directory (copied to a test fixture) produces
    `implement` ×3 + `simplify` ×1 + `verify` ×1; inline stages show `stage=None`
    because build-90 predates marker emission.
  passes: true
  waived: false
  waiver_reason: null
- id: ac-06
  text: Every LLM-invoking `.md` template in `claude/commands/mantle/` begins with
    `mantle stage-begin <name>`. Parity harness (`tests/parity/`) snapshots refreshed
    for all affected integrated commands.
  passes: true
  waived: false
  waiver_reason: null
- id: ac-07
  text: '`BuildReport` stays backward-compatible — pre-existing `.mantle/builds/build-NN-*.md`
    files load without error; `stage=None` renders as "Unattributed".'
  passes: true
  waived: false
  waiver_reason: null
- id: ac-08
  text: '`just check` passes — ruff + ty + pytest, import-linter contracts unchanged.'
  passes: true
  waived: false
  waiver_reason: null
---

## Parent PRD

product-design.md, system-design.md

## Why

Build telemetry is half-broken and standalone commands are entirely unattributed.

Two diagnoses from issue 89's shaping converge here:

1. **Sub-agent transcripts live in a separate location.** Build-90's session JSONL has 188 assistant turns, all `isSidechain: false`. Its 5 sub-agent spawns (3× story-implementer, 1× refactorer, 1× general-purpose) live at `~/.claude/projects/<proj>/<parent_session>/subagents/agent-*.jsonl`. `telemetry.find_session_file` + `telemetry.read_session` only read the parent JSONL, so sub-agent usage is invisible and `group_stories` always returns `()`.

2. **Inline stages have no attribution.** Shape and plan_stories run as parent-session turns inside the build orchestrator; there is no mechanism today to attribute those turns to a stage. Outside the build pipeline, standalone `/mantle:shape-issue` / `/mantle:verify` / etc. runs are invisible to any aggregator — `audit-tokens` and issue 89's A/B harness cannot slice cost by stage for them.

The user's constraint surfaced during shaping: stage attribution must work for **every LLM-invoking Mantle command, inside or outside `/mantle:build`**. That collapses "build stages" and "standalone commands" into one concept: a stage is any named Mantle command that does LLM reasoning.

See `.mantle/shaped/issue-92-per-stage-build-telemetry-sub-shaped.md` (Approach D-revised) for the full analysis. This issue is the prerequisite for issue 89 (A/B harness AC-02 requires per-stage cost/time).

## Blocks

Issue 89 (A/B harness).

## What to build

Four cohesive additions.

**1. New module `src/mantle/core/stages.py`** — stage-begin primitive.

- `StageMark` pydantic model (frozen): `{stage: str, at: datetime}` — on-disk event shape.
- `StageWindow` pydantic model (frozen): `{stage: str, start: datetime, end: datetime}` — parser-side half-open interval.
- `record_stage(stage, project_dir=None) -> None` — resolves session id via `telemetry.current_session_id`; appends one JSONL line to `<project_dir>/.mantle/telemetry/stages-<session_id>.jsonl` (creating the directory if absent). Silent no-op when no session id is resolvable.
- `read_stages(session_id, project_dir=None) -> tuple[StageMark, ...]` — parses the session's JSONL in chronological order; malformed lines silently skipped; returns `()` when absent.
- `windows_for_session(marks, session_end) -> tuple[StageWindow, ...]` — pure function; produces half-open windows, each closing at the next mark's `at` or at `session_end` for the last mark.

Depends only on `core.telemetry` (for `current_session_id`) + stdlib.

**2. Extend `src/mantle/core/telemetry.py`** — sub-agent read path.

- `SubagentMeta` pydantic model (frozen, `extra="ignore"` — Claude Code owns schema): `agent_type: str = Field(alias="agentType")`.
- Widen `StoryRun` with `stage: str | None = None`.
- `find_subagent_files(parent_session_id, projects_root=None) -> tuple[Path, ...]` — glob `<parent>/subagents/agent-*.jsonl`; sort by first-turn timestamp.
- `read_subagent(jsonl_path) -> tuple[Turn, ...]` — reuse `_parse_assistant_line`; sub-agent files have the same turn shape with `isSidechain: true`.
- `read_meta(jsonl_path) -> SubagentMeta | None` — parse sibling `agent-*.meta.json`; None on absence/malformed.
- Private mapping `_AGENT_TYPE_TO_STAGE = {story-implementer: implement, refactorer: simplify, general-purpose: verify}`. Unknown types → `stage=None`.
- Rewrite `group_stories(parent_turns, subagent_paths=(), stage_windows=()) -> tuple[StoryRun, ...]` — one `StoryRun` per sub-agent file (stage from meta) plus one per `StageWindow` that overlaps the parent session (aggregating parent turns inside the window). Sorted by `started`.
- `render_report` groups stories by `stage`, with "Unattributed" bucket for `stage=None`.
- **Deletions:** `_aggregate_cluster`'s sidechain-cluster branch, `Marker`, `MarkerWindowWarning`, `_attach_story_ids`, plus `cli/builds.py:_derive_mtime_markers`. All served the parent-sidechain clustering unreachable against current Claude Code builds.

**3. New CLI command `mantle stage-begin <name>`** in `src/mantle/cli/main.py` under `GROUPS["impl"]`.

```python
@app.command(name="stage-begin", group=GROUPS["impl"])
def stage_begin_command(name: str) -> None:
    """Mark the start of a named stage in the current session."""
    stages.record_stage(name)
```

No flags. Single positional arg. Graceful no-op when no session id is resolvable. Validates only "non-empty" — typos in template edits are caught via parity-harness snapshot review.

**4. Template edits across `claude/commands/mantle/`**

Add `mantle stage-begin <stage-name>` as the first shell call in every LLM-invoking `.md` template. Stage name matches the `cost-policy.md` key (`shape`, `plan_stories`, `implement`, `simplify`, `verify`, `review`, `retrospective`) where applicable, or the command slug otherwise (`build`, `challenge`, `design-product`, `design-system`, `revise-product`, `revise-system`, `brainstorm`, `research`, `scout`, `adopt`, `refactor`, `plan-issues`, `idea`, `patterns`, `distill`, `fix`).

Proposed skip list (implementer refines at story time): `help.md`, `resume.md.j2`, `status.md.j2`, `add-issue.md`, `add-skill.md`, `bug.md`, `inbox.md`, `query.md` — wiring or short non-reasoning commands.

`build.md` additionally emits `mantle stage-begin shape` at the start of Step 4 and `mantle stage-begin plan_stories` at the start of Step 5, since those stages run inline in the parent session.

**5. `build-finish` wiring** in `src/mantle/cli/builds.py`

`run_build_finish`:
1. Read parent session JSONL (unchanged).
2. `stages.read_stages(session_id)` → `stages.windows_for_session(marks, report.finished)`.
3. `telemetry.find_subagent_files(session_id)`.
4. `telemetry.group_stories(parent_turns, subagent_paths, stage_windows)`.
5. Render.

## Acceptance criteria

- [x] ac-01: `mantle stage-begin <name>` appends a well-formed JSONL `StageMark` to `.mantle/telemetry/stages-<session_id>.jsonl` when a Claude Code session id is resolvable; no-ops silently otherwise. Creates `.mantle/telemetry/` if absent.
- [x] ac-02: `telemetry.group_stories()` returns one `StoryRun` per sub-agent JSONL under `<parent>/subagents/`, with `stage` populated from `agentType` via `story-implementer→implement`, `refactorer→simplify`, `general-purpose→verify`; unknown types yield `stage=None`.
- [x] ac-03: Parent-session inline turns are attributed to a stage when a `StageWindow` overlaps their timestamp; turns outside any window get `stage=None` (rendered as "Unattributed").
- [x] ac-04: Synthetic roundtrip fixture (parent JSONL + `subagents/` dir + `stages-<session_id>.jsonl`) renders a build report whose `stories:` frontmatter contains stage-grouped rows per `inline_snapshot` capture.
- [x] ac-05: Re-parsing build-90's real session directory (copied to a test fixture) produces `implement` ×3 + `simplify` ×1 + `verify` ×1; inline stages show `stage=None` because build-90 predates marker emission.
- [x] ac-06: Every LLM-invoking `.md` template in `claude/commands/mantle/` begins with `mantle stage-begin <name>`. Parity harness (`tests/parity/`) snapshots refreshed for all affected integrated commands.
- [x] ac-07: `BuildReport` stays backward-compatible — pre-existing `.mantle/builds/build-NN-*.md` files load without error; `stage=None` renders as "Unattributed".
- [x] ac-08: `just check` passes — ruff + ty + pytest, import-linter contracts unchanged.

## Does not

- Emit `stage-end`. Single-event marks only; next `stage-begin` implicitly closes the previous window.
- Retroactively attribute historical builds. Pre-existing build files keep `stage=None` on inline turns.
- Disambiguate `general-purpose` beyond the build-context `verify` mapping. A future non-verify caller of `general-purpose` would read incorrectly — acceptable while `build.md` is the only caller.
- Rotate or compact `stages-*.jsonl`. Old sessions' files can be deleted manually if they accumulate.
- Add price application to `StoryRun` — belongs to `core/ab_build.py` (issue 89 scope).
- Instrument plumbing CLI calls (`mantle update-story-status`, `mantle save-shaped-issue`, etc.) or the skip-list templates.

## Blocked by

None.

## User stories addressed

- As a Mantle maintainer evaluating per-stage model choices, I want build reports to contain per-stage cost/time so preset trade-offs are measurable, not vibes.
- As a developer running `/mantle:build`, I want the resulting build-NN-*.md to actually reflect what the pipeline did, so retrospectives have real data.
- As a developer running a standalone `/mantle:shape-issue` or `/mantle:verify`, I want the session's token usage to be attributable to that stage — not lumped into an un-named bucket.

## Notes

- Full design: `.mantle/shaped/issue-92-per-stage-build-telemetry-sub-shaped.md` (Approach D-revised).
- Diagnosis fixture session id: `514d3e78-4614-4206-a4c1-4f26dafe9e10` (build-90, 2026-04-24).
- `.meta.json` sidecar schema is a Claude Code-owned contract. Parse defensively; fall back to `stage=None` on any schema surprise.
- Storage location `.mantle/telemetry/stages-<session_id>.jsonl` — per-session file in the existing telemetry folder. Co-locates with `baseline-*.md/.json` artefacts and eliminates cross-worktree write races by construction.
- Parity harness (issue 90) catches template-edit drift automatically; expect snapshot refresh on every touched template.
