---
issue: 92
title: 'build-finish wiring: read stages + sub-agent files, drop _derive_mtime_markers'
status: planned
failure_log: null
tags:
- type/story
- status/planned
---

## User Story

As a developer whose `/mantle:build` just completed, I want the generated `build-NN-*.md` report to contain real per-stage cost/time attribution sourced from stage marks + sub-agent JSONLs, so that retrospectives have real data and issue 89's A/B harness can slice cost by stage.

## Depends On

Stories 1 and 3 — uses `core.stages.read_stages` + `core.stages.windows_for_session` and the rewritten `telemetry.group_stories(parent_turns, subagent_paths, stage_windows)`.

## Approach

Rewrite `cli/builds.py:run_build_finish` to read three telemetry sources (parent session JSONL, per-session stage-marks JSONL, sub-agent JSONLs) and feed them to the new `group_stories` signature. Delete `_derive_mtime_markers` and the `_STORY_FILENAME_RE` regex that only served it. Update `render_report` call site to match its new signature (no `markers` arg).

## Implementation

### src/mantle/cli/builds.py (modify)

**1. Update imports.** Add:

```python
from mantle.core import stages
```

Remove `re` import (only `_STORY_FILENAME_RE` used it).

**2. Rewrite `run_build_finish`.** After the existing guard clauses (missing stub, missing session_id, missing session_file), replace the body that calls `_derive_mtime_markers` + old `group_stories` with:

```python
marks = stages.read_stages(session_id, project_dir)
parent_turns = telemetry.read_session(session_file)

# Build windows using the last parent-turn timestamp as session_end
# (falls back to now(UTC) when the session has zero turns).
if parent_turns:
    session_end = max(t.timestamp for t in parent_turns)
else:
    session_end = datetime.now(UTC)
stage_windows = stages.windows_for_session(marks, session_end)

subagent_paths = telemetry.find_subagent_files(session_id)

runs = telemetry.group_stories(
    parent_turns=parent_turns,
    subagent_paths=subagent_paths,
    stage_windows=stage_windows,
)
report = telemetry.summarise(session_id, parent_turns, runs)
rendered = telemetry.render_report(report, issue=issue)  # no markers arg
```

**3. Delete `_derive_mtime_markers`** and the `_STORY_FILENAME_RE` constant at module level.

**4. Leave `_find_latest_in_progress_stub`, `_read_frontmatter_value`, `_finalize_frontmatter` unchanged.**

#### Design decisions

- **`session_end` from last parent turn**: in practice `run_build_finish` is called immediately after the build orchestrator finishes, so the last parent turn's timestamp is within seconds of `now()`. Using the last turn avoids pulling in a clock call when the session has data; the `datetime.now(UTC)` fallback covers the empty-session edge case (Claude Code wrote no assistant turns — rare but possible).
- **Order of reads**: parent turns first because they anchor `session_end`; stage marks convert to windows against that; sub-agent paths are independent but sorted by first-turn timestamp inside `find_subagent_files` so overall output is already chronological.
- **No fallback to old clustering**: `find_subagent_files` returns `()` cleanly on older sessions predating the split layout; `group_stories` handles empty gracefully → empty `stories:` list in the rendered report. This is acceptable degradation — pre-existing builds display the same \"No story runs detected\" as today.
- **Drop `markers` from `render_report` call**: Story 3 removes the parameter; this site was the only caller passing it.

## Tests

### tests/cli/test_builds.py (modify, add, or create if absent)

Keep all existing tests for `run_build_start`, `_find_latest_in_progress_stub`, `_read_frontmatter_value`, `_finalize_frontmatter`. Delete any test that exercises `_derive_mtime_markers` (it's being removed).

Add new tests for the integrated flow. Use `tmp_path` as the \"project root\"; synthesise a fake Claude Code projects directory inside it and point `CLAUDE_PROJECTS_DIR` + `CLAUDE_SESSION_ID` at it.

- **test_run_build_finish_roundtrip_with_subagents**: set up `tmp_path/projects/<slug>/<sid>.jsonl` (parent turns with 2 assistant turns), `tmp_path/projects/<slug>/<sid>/subagents/agent-1.jsonl` + `agent-1.meta.json` (agentType=story-implementer), and `tmp_path/.mantle/telemetry/stages-<sid>.jsonl` with one StageMark for `shape` before the parent turn timestamps. Write a build stub, monkeypatch env vars, call `run_build_finish(issue=99, project_dir=tmp_path)`. Use `inline_snapshot` on the resulting build file body (normalised for timestamps via a small helper) to assert a stage-grouped `## Summary` section and a `stories:` list with two entries (implement + shape).
- **test_run_build_finish_no_stages_no_subagents**: only parent JSONL + stub; no stages file; no subagents dir. `run_build_finish` still finalises the stub with empty `stories:`. No exceptions raised.
- **test_run_build_finish_empty_parent_session**: parent JSONL with zero assistant turns, no subagents, no stages. Report still finalises with `session_end = datetime.now(UTC)` window-closing behaviour; empty stories list renders.
- **test_run_build_finish_drops_old_markers_contract**: call `run_build_finish` in a setup where a `stories/` directory contains `issue-99-story-*.md` files. Result's `stories:` list is NOT driven by those files (confirms `_derive_mtime_markers` is gone).

#### Test fixture requirements

- `tmp_path` throughout.
- `monkeypatch.setenv('CLAUDE_SESSION_ID', 'test-sid')` + `monkeypatch.setenv('CLAUDE_PROJECTS_DIR', str(tmp_path / 'projects'))`.
- Synthesise parent + sub-agent JSONLs programmatically via a small `_write_jsonl(path, turns)` helper — inline in the test file.
- For timestamp-sensitive snapshots, normalise via `re.sub(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?([+-]\d{2}:\d{2}|Z)?', '<TS>', body)` before passing to `inline_snapshot`.

## Verification against issue ACs

- **ac-04**: `test_run_build_finish_roundtrip_with_subagents` asserts the full rendered report via inline snapshot.
- **ac-07**: `test_run_build_finish_no_stages_no_subagents` + `test_run_build_finish_empty_parent_session` confirm backward compatibility.