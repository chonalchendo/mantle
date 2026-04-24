---
issue: 92
title: 'Telemetry: sub-agent read path + stage attribution + group_stories rewrite'
status: planned
failure_log: null
tags:
- type/story
- status/planned
---

## User Story

As a developer running `/mantle:build`, I want telemetry to read sub-agent JSONLs and attribute each `StoryRun` to a named stage, so that build reports surface real per-stage cost/time instead of `No story runs detected`.

## Depends On

Story 1 — imports `StageWindow` from `core.stages`.

Independent of Story 2 — this story adds the parser-side read path; Story 2 adds the writer-side CLI. They compose but can be implemented in parallel.

## Approach

Extend `core/telemetry.py` with three new readers (`find_subagent_files`, `read_subagent`, `read_meta`), a new `SubagentMeta` model, a `stage` field on `StoryRun`, and a rewritten `group_stories` that clusters by sub-agent file + overlapping `StageWindow`. Delete the dead parent-sidechain clustering along with `Marker`, `MarkerWindowWarning`, `_attach_story_ids`, and `MARKER_WINDOW_SECONDS` — grep confirms the only caller is `cli/builds.py:_derive_mtime_markers` (removed in Story 4).

## Implementation

### src/mantle/core/telemetry.py (modify)

**1. Add `SubagentMeta` model.** After `Usage` / before `Turn`:

```python
class SubagentMeta(pydantic.BaseModel, frozen=True):
    \"\"\"Parsed `agent-*.meta.json` sidecar.

    Claude Code owns this schema; use `extra='ignore'` so new fields
    upstream never break parsing.
    \"\"\"

    model_config = pydantic.ConfigDict(extra=\"ignore\")

    agent_type: str = pydantic.Field(alias=\"agentType\")
```

**2. Widen `StoryRun`.** Add one optional field at the end (non-breaking for existing constructors):

```python
stage: str | None = None
```

Update the docstring to mention the new field (`stage: Stage name attributed to this run, or None when unknown.`).

**3. Add the agent-type → stage mapping.** Near the constants section:

```python
_AGENT_TYPE_TO_STAGE: Mapping[str, str] = {
    \"story-implementer\": \"implement\",
    \"refactorer\": \"simplify\",
    \"general-purpose\": \"verify\",
}
```

Import `Mapping` from `collections.abc`.

**4. Add `find_subagent_files`.**

```python
def find_subagent_files(
    parent_session_id: str,
    projects_root: Path | None = None,
) -> tuple[Path, ...]:
    \"\"\"Locate sub-agent JSONLs for a parent Claude Code session.

    Resolution order matches `find_session_file`: `projects_root`
    arg → `CLAUDE_PROJECTS_DIR` env → `~/.claude/projects`. Sub-agent
    transcripts live at
    `<projects_root>/<slug>/<parent_session_id>/subagents/agent-*.jsonl`.

    Returns tuple sorted by the file's first-turn timestamp so the
    caller sees chronologically ordered runs. Empty tuple when the
    `subagents/` directory is absent (common for older sessions
    predating the split file layout).
    \"\"\"
```

Behaviour: reuse `_resolve_projects_root`. Glob `<root>/*/<parent>/subagents/agent-*.jsonl`. For each file, peek the first line via `_parse_assistant_line` to get `timestamp`; fall back to `path.stat().st_mtime` if no parseable turn. Return tuple sorted ascending by that timestamp.

**5. Add `read_subagent`.**

```python
def read_subagent(jsonl_path: Path) -> tuple[Turn, ...]:
    \"\"\"Parse a sub-agent JSONL into assistant turns.

    Sub-agent files use the same record shape as parent sessions —
    one assistant turn per line, with `isSidechain: true` already
    set. Reuses the parent-session parser.
    \"\"\"
    return read_session(jsonl_path)
```

Pure delegation — the file formats are identical. Keeping the distinct name documents intent at call sites.

**6. Add `read_meta`.**

```python
def read_meta(jsonl_path: Path) -> SubagentMeta | None:
    \"\"\"Parse the sibling `agent-*.meta.json` sidecar.

    Given `<dir>/agent-<id>.jsonl`, reads `<dir>/agent-<id>.meta.json`.
    Returns None when the sidecar is absent or malformed — callers
    degrade gracefully to `stage=None`.
    \"\"\"
```

Behaviour: derive `meta_path = jsonl_path.with_suffix('').with_suffix('.meta.json')` — actually, use `jsonl_path.with_name(jsonl_path.stem + \".meta.json\")` to be unambiguous (path has `.jsonl` suffix). Read the file; `json.loads` it; `SubagentMeta.model_validate(data)`; on `FileNotFoundError`, `json.JSONDecodeError`, `pydantic.ValidationError`, `OSError` return `None`.

**7. Rewrite `group_stories`.** New signature:

```python
def group_stories(
    parent_turns: tuple[Turn, ...] = (),
    subagent_paths: tuple[Path, ...] = (),
    stage_windows: tuple[\"stages.StageWindow\", ...] = (),
) -> tuple[StoryRun, ...]:
    \"\"\"Produce per-stage `StoryRun` records from three sources.

    - One run per sub-agent JSONL path, stage attributed via the
      sidecar's `agentType` through `_AGENT_TYPE_TO_STAGE`. Unknown
      types yield `stage=None`.
    - One run per `StageWindow` that overlaps any parent turn; the
      run aggregates all parent turns with timestamp inside the
      half-open `[start, end)` interval.
    - Results sorted ascending by `started`.
    \"\"\"
```

Import `stages` lazily via `from __future__ import annotations` (already present) + `if TYPE_CHECKING: from mantle.core import stages`. Actual use is runtime — runtime import inside function body to avoid circular import: `from mantle.core import stages as _stages`.

Behaviour:

1. For each path in `subagent_paths`: call `read_subagent(path)` → turns. Call `read_meta(path)` → meta. Skip if turns is empty. Compute `agent_type = meta.agent_type if meta else None`; `stage = _AGENT_TYPE_TO_STAGE.get(agent_type) if agent_type else None`. Call `_aggregate_cluster(list(turns))` to get a StoryRun. Replace its stage via `run.model_copy(update={'stage': stage})`.
2. For each window in `stage_windows`: gather `parent_turns` where `window.start <= turn.timestamp < window.end`. Skip windows with no matching turns. Aggregate via `_aggregate_cluster`; set `stage=window.stage`.
3. Concatenate both lists; sort by `started`; return tuple.

**8. Update `render_report`.** Group stories by stage in the rendered table:

```python
def render_report(report: BuildReport, issue: int) -> str:
```

(Remove the `markers` parameter — it's dead. Update callers in Story 4.)

Change the summary table: group by `stage` with a sub-heading per stage; unknown stages go into an `Unattributed` bucket at the end. Example:

```markdown
## Summary

### implement
| Story | Model | Duration (s) | Turns | In tok | Out tok |
...

### simplify
...

### verify
...

### Unattributed
...
```

Keep the frontmatter `stories:` list emitting every run with its `stage: <name>` or `stage: null`.

**9. Deletions.** Remove:

- `Marker` class.
- `MarkerWindowWarning` class.
- `MARKER_WINDOW_SECONDS` constant.
- `_attach_story_ids` function.
- The old `group_stories` signature/body (replaced by new signature above).
- The `import warnings` import (no longer used).

Confirm via grep that nothing else in the codebase imports `Marker` or `MarkerWindowWarning`. If anything does outside `cli/builds.py`, flag it — Story 4 will need to fix it.

#### Design decisions

- **Deep-module extension over new module**: `core/telemetry.py` absorbs one more clustering strategy into its existing narrow public interface; keeping the parser-side concepts in one file makes the stage-attribution contract obvious.
- **`extra='ignore'` on `SubagentMeta`**: Claude Code owns the `.meta.json` schema; new upstream fields must not break us. Mirrors `sqlmesh`/`pydantic-project-conventions` guidance on external schemas.
- **Runtime `stages` import inside `group_stories`**: keeps `core/telemetry.py` independent of `core/stages.py` at module load, preventing circular import while allowing StageWindow typing in the signature.
- **`_AGENT_TYPE_TO_STAGE` is internal**: callers see only `StoryRun.stage`. Disambiguating `general-purpose` for non-build callers is explicitly out of scope (see issue body's `Does not` section).
- **Delete `Marker` cleanly, no deprecation shim**: current builds have zero parent-sidechain turns, so the old API is unreachable dead code. CLAUDE.md's \"avoid backwards-compatibility shims\" rule applies.

## Tests

### tests/core/test_telemetry.py (modify)

Delete tests that exercise `Marker`, `_attach_story_ids`, `MarkerWindowWarning`, or the old `group_stories(turns, markers)` signature. Keep all tests that exercise `read_session`, `summarise`, `find_session_file`, `_parse_assistant_line`.

Add new tests:

- **test_read_meta_parses_agent_type**: write `tmp_path/agent-123.meta.json` with `{\"agentType\": \"story-implementer\", \"otherField\": \"ignored\"}`; `read_meta(tmp_path/'agent-123.jsonl')` returns `SubagentMeta(agent_type='story-implementer')`.
- **test_read_meta_missing_returns_none**: no sidecar → None.
- **test_read_meta_malformed_returns_none**: sidecar with invalid JSON → None.
- **test_read_meta_missing_agent_type_returns_none**: sidecar with `{}` → None (validation fails).
- **test_find_subagent_files_returns_sorted**: tmp projects root with slug dir + parent/subagents dir + two agent JSONLs whose first-turn timestamps are T1 > T0; assert returned tuple is `(path_with_T0, path_with_T1)`.
- **test_find_subagent_files_empty_when_absent**: parent session dir exists but no `subagents/` child → `()`.
- **test_read_subagent_parses_sidechain_turns**: JSONL with 3 assistant turns all `isSidechain: true`; `read_subagent` returns 3 Turns preserving `is_sidechain=True`.
- **test_group_stories_from_subagent_paths**: 3 sub-agent paths with meta sidecars (`story-implementer`, `refactorer`, `general-purpose`); stage_windows empty; parent_turns empty; assert result is 3 StoryRuns with stages `implement`, `simplify`, `verify`.
- **test_group_stories_unknown_agent_type_yields_stage_none**: sub-agent with `agentType: \"custom-thing\"` in sidecar → StoryRun with `stage=None`.
- **test_group_stories_from_stage_windows**: parent_turns with 4 turns at T0..T3; stage_windows = `[StageWindow(stage='shape', start=T0, end=T2), StageWindow(stage='plan_stories', start=T2, end=T4)]`; assert 2 StoryRuns with correct stages and turn counts (2 each).
- **test_group_stories_window_with_no_turns_is_skipped**: window covering empty interval → no StoryRun emitted for it.
- **test_group_stories_half_open_windows**: turn exactly at `window.end` is NOT included (half-open); turn at `window.start` IS included.
- **test_group_stories_results_sorted_by_started**: mix sub-agent runs + window runs with interleaved timestamps; assert output sorted ascending by `started`.
- **test_group_stories_empty_returns_empty**: all three args empty → `()`.

### tests/core/test_telemetry_render.py (new file — or extend test_telemetry.py)

- **test_render_report_groups_by_stage**: BuildReport with StoryRuns stages `implement` ×2 + `simplify` ×1 + `verify` ×1 + None ×1; render; assert four `###` sub-headings (`implement`, `simplify`, `verify`, `Unattributed`) in that order. Use `inline_snapshot` for the full rendered markdown.
- **test_render_report_empty_stories**: empty stories tuple → renders with \"No story runs detected\" placeholder (back-compat).
- **test_render_report_all_unattributed**: only stage=None runs → only `Unattributed` section.

### tests/fixtures/build-90-session/ (new directory)

Copy the real files from `~/.claude/projects/-Users-conal-Development-mantle/514d3e78-4614-4206-a4c1-4f26dafe9e10/` into `tests/fixtures/build-90-session/`:

- The parent `514d3e78-4614-4206-a4c1-4f26dafe9e10.jsonl` (truncate to a small subset if > 1MB — keep at least one assistant turn).
- All 5 `subagents/agent-*.jsonl` files + their `agent-*.meta.json` sidecars.

Document provenance in a `tests/fixtures/build-90-session/README.md`: `\"Captured from session 514d3e78... on 2026-04-24 for issue 92 regression test.\"`

### tests/core/test_build90_fixture.py (new file)

- **test_build90_produces_three_implement_one_simplify_one_verify**: point `find_subagent_files` at the fixture's parent dir (via `projects_root=tests/fixtures/` and synthetic slug dir structure matching `<slug>/<sid>/subagents/`); call `group_stories(parent_turns=(), subagent_paths=subagent_paths, stage_windows=())`; assert `Counter(run.stage for run in runs) == Counter({'implement': 3, 'simplify': 1, 'verify': 1})`.

Use `dirty_equals.IsList(check_order=False)` for the Counter-equivalent comparison, or just `Counter(...) == Counter(...)` — simpler.

#### Test fixture requirements

- Use `tmp_path` for all filesystem writes in unit tests.
- Use checked-in `tests/fixtures/build-90-session/` for the real-data regression test — data is small and provenance is documented.
- Timestamp freezing not needed — we're parsing fixed content, not calling `datetime.now`.

## Verification against issue ACs

- **ac-02**: `test_group_stories_from_subagent_paths` + `test_group_stories_unknown_agent_type_yields_stage_none`.
- **ac-03**: `test_group_stories_from_stage_windows` + `test_group_stories_half_open_windows`.
- **ac-05**: `test_build90_produces_three_implement_one_simplify_one_verify`.
- **ac-07** (partial — full integration in Story 4): render changes verified by `test_render_report_groups_by_stage`.