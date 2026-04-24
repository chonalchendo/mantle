---
title: 'Fix build telemetry: read sub-agent JSONLs + add per-stage attribution'
status: planned
slice:
- core
- tests
story_count: 0
verification: null
blocked_by: []
skills_required: []
tags:
- type/issue
- status/planned
acceptance_criteria: []
---

## Parent PRD

product-design.md, system-design.md

## Why

Build telemetry is half-broken. Issue 91 fixed `.mantle/.session-id` writing, but build-90's report still says "No story runs detected" — because sub-agent transcripts live in a separate location (`~/.claude/projects/<proj>/<parent_session_id>/subagents/agent-<id>.jsonl`), not as sidechain turns in the parent session's JSONL.

Diagnosis (done during issue 89's shaping session):
- Build-90 session JSONL has 188 assistant turns, all with `isSidechain: false`.
- Agent tool was invoked 5 times: 3× story-implementer + 1× refactorer + 1× general-purpose.
- Sub-agent JSONLs exist at `~/.claude/projects/-Users-conal-Development-mantle/514d3e78-4614-4206-a4c1-4f26dafe9e10/subagents/agent-*.jsonl` (5 of them, plus `.meta.json` sidecars).
- `telemetry.find_session_file` and `telemetry.read_session` only read the parent JSONL, so sub-agent usage is invisible.
- Sub-agent JSONLs have `isSidechain: true` on their turns and carry model/usage data.

This issue fixes that read path. It also seizes the opportunity to add per-stage attribution — the `.meta.json` sidecars expose `subagent_type` (`story-implementer` → `implement`, `refactorer` → `simplify`, `general-purpose` → `verify` or `shape` depending on position), which makes per-stage cost reporting possible for the first time.

## Blocks

Issue 89 (A/B harness) cannot enter `/mantle:plan-stories` until this lands — its AC-02 requires per-stage cost/time.

## What to build

Core changes in `src/mantle/core/telemetry.py`:

1. New function: `find_subagent_files(parent_session_id, projects_root=None) -> tuple[Path, ...]` — returns all `<parent>/subagents/agent-*.jsonl` paths.
2. New function: `read_subagent(jsonl_path) -> tuple[Turn, ...]` — same as `read_session` but for sub-agent files. These already have `isSidechain: true`; one file per Agent spawn.
3. New function: `read_meta(jsonl_path) -> SubagentMeta` — parses the sibling `agent-*.meta.json` for `subagent_type`, spawn model, etc.
4. Widen `StoryRun` model: add `stage: str | None` field.
5. Rewrite `group_stories()` — replace parent-uuid clustering (which was operating on the wrong file) with "one StoryRun per subagent file." Attribute `stage` via `subagent_type`:
   - `story-implementer` → `"implement"`
   - `refactorer` → `"simplify"`
   - `general-purpose` → `"verify"` (when invoked by build.md Step 8; may need context disambiguation for other callers — see Open Questions)
6. Widen `find_session_file` or add a companion function that returns both parent and sub-agent paths.
7. Extend `render_report` to group `stories:` by stage when `stage` is populated.

Optional (can defer to a follow-up if scope balloons):
- Inline-stage attribution (shape, plan_stories — which run in parent-session turns, not sub-agents). One approach: emit stage markers from the build orchestrator (`mantle stage-begin shape` / `stage-end shape`) that append to a sidecar file; parser slices parent-session turns by time window.

## Acceptance criteria

- [ ] ac-01: `telemetry.group_stories()` returns one `StoryRun` per sub-agent JSONL found under `<parent>/subagents/`.
- [ ] ac-02: Each `StoryRun.stage` is populated from the matching `.meta.json`'s `subagent_type`, using the mapping `story-implementer→implement`, `refactorer→simplify`, `general-purpose→verify` (build context).
- [ ] ac-03: A roundtrip test fixture — parent JSONL + synthetic `subagents/` directory — asserts the rendered build report contains a non-empty `stories:` frontmatter list with per-stage attribution.
- [ ] ac-04: Re-parsing build-90's actual session (via a test fixture copied from `~/.claude/projects/...`) produces a non-empty stories list with 3× implement + 1× simplify + 1× verify.
- [ ] ac-05: The `BuildReport` model stays backward-compatible with existing build-*.md files (new fields default safely; render changes do not break older parsers).
- [ ] ac-06: `just check` passes — ruff + ty + pytest, import-linter contracts unchanged.

## Blocked by

None. This is the blocker for 89.

## User stories addressed

- As a Mantle maintainer evaluating per-stage model choices, I want build reports to contain per-stage cost/time so preset trade-offs are measurable, not vibes.
- As a developer running `/mantle:build`, I want the resulting build-NN-*.md to actually reflect what the pipeline did, so later retrospectives have real data.

## Notes

- Diagnosis done during issue 89's shaping session, 2026-04-24. See `.mantle/shaped/issue-89-ab-harness-for-build-pipeline-shaped.md` for context.
- The parent-session's own turns still carry real token usage (for the inline shape/plan_stories work) — attributing those is the "optional" extension and may warrant its own follow-up issue.
- `.meta.json` sidecar schema is an external-to-mantle contract owned by Claude Code. Parse it defensively; fall back to `stage=None` if keys are missing.
- Session id for the diagnosis fixture: `514d3e78-4614-4206-a4c1-4f26dafe9e10` (build-90, 2026-04-24).