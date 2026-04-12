---
issue: 54
title: Core telemetry parser — JSONL session data to StoryRun records
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a build orchestrator, I want a pure parser that converts Claude Code session JSONL into per-story telemetry records so that downstream build reports have accurate model/token/duration data without relying on LLM self-reporting.

## Depends On

None — independent.

## Approach

New pure module `src/mantle/core/telemetry.py` that reads a Claude Code session JSONL file (located under `~/.claude/projects/<slug>/<session-uuid>.jsonl`), parses assistant turns, groups sidechain clusters (`isSidechain: true`) by parent chain, and aggregates them into per-story runs. Pydantic frozen models mirror the Anthropic issue #22625 proposed schema for forward compatibility. Pure function pipeline: `read_session → group_stories → summarise`. Respects the CLAUDE.md rule: `core/` never imports from `cli/`.

## Implementation

### src/mantle/core/telemetry.py (new file)

Module docstring: `\"Parse Claude Code session JSONL into per-story telemetry records.\"`

Imports: `from __future__ import annotations`, `json`, `pathlib.Path`, `datetime`, `os`, `pydantic`.

#### Data models (all `pydantic.BaseModel, frozen=True`)

- `Usage(input_tokens: int, output_tokens: int, cache_read_input_tokens: int = 0, cache_creation_input_tokens: int = 0)` — token breakdown from `message.usage`. Add field aliases only if needed; the JSONL uses these exact keys.
- `Turn(uuid: str, parent_uuid: str | None, session_id: str, timestamp: datetime, model: str | None, is_sidechain: bool, usage: Usage | None)` — one assistant turn parsed from JSONL.
- `StoryRun(story_id: int | None, model: str, started: datetime, finished: datetime, duration_s: float, usage: Usage, turn_count: int)` — aggregated sidechain cluster. `story_id` is optional — populated when `markers` supplied.
- `Marker(story_id: int, timestamp: datetime)` — orchestrator-supplied signal that maps story id to a wall-clock timestamp.
- `BuildReport(session_id: str, started: datetime, finished: datetime, stories: tuple[StoryRun, ...])` — summarised build.

#### Public functions

- `find_session_file(session_id: str, projects_root: Path | None = None) -> Path` — resolves `~/.claude/projects/*/<session_id>.jsonl`. `projects_root` defaults to `Path.home() / \".claude\" / \"projects\"`. Raises `FileNotFoundError` with a clear message if not found. Honour `CLAUDE_PROJECTS_DIR` env var if set (for CI portability).
- `read_session(session_file: Path) -> tuple[Turn, ...]` — iterate JSONL, parse only `{\"type\": \"assistant\"}` records. Skip malformed lines (do not raise). Return turns in file order.
- `group_stories(turns: tuple[Turn, ...], markers: tuple[Marker, ...] = ()) -> tuple[StoryRun, ...]` — cluster sidechain turns sharing a parent chain root. A new cluster starts when a sidechain turn's `parent_uuid` is not in the current cluster's uuid set (i.e. it's a fresh Agent spawn). Attach `story_id` by matching each cluster's earliest timestamp to the closest marker preceding it (within a reasonable window — suggest 60s cap, warn if exceeded). Aggregate `Usage` by summing fields; `model` is the mode (most frequent) across the cluster.
- `summarise(session_id: str, turns: tuple[Turn, ...], story_runs: tuple[StoryRun, ...]) -> BuildReport` — derive overall `started`/`finished` from all turns' timestamp range.

#### Design decisions

- **Pydantic frozen models**: match project convention (`core/session.py`, `core/stories.py`).
- **`tuple` return types**: hashable, immutable — project convention.
- **No mutation, no I/O except reading**: pure core module.
- **Correlation via markers, not uuid-capture**: markers are cheaper — orchestrator already calls `mantle update-story-status --in-progress` per story, which gives us a timestamped signal. Uuid-capture would require deeper instrumentation.
- **Skip malformed JSONL lines instead of raising**: real-world transcripts may contain partial writes; being lenient keeps reports producible.
- **Import style**: `from mantle.core import ...` elsewhere imports; this module has no internal mantle deps, only stdlib + pydantic.

## Tests

### tests/core/test_telemetry.py (new file)

Use `tmp_path` to build synthetic JSONL fixtures. Do not hit real `~/.claude/`.

- **test_find_session_file_success**: creates `tmp/projects/-some-slug/<uuid>.jsonl`, `find_session_file(uuid, tmp/projects)` returns its path.
- **test_find_session_file_missing_raises**: unknown session id raises `FileNotFoundError` with session id in message.
- **test_find_session_file_honours_env_var** (monkeypatch `CLAUDE_PROJECTS_DIR`): picks up custom root.
- **test_read_session_parses_assistant_turns**: JSONL with 3 assistant + 1 user record → 3 turns returned; user record filtered out.
- **test_read_session_skips_malformed_lines**: JSONL with one half-written line → valid turns still returned.
- **test_read_session_parses_usage_fields**: assistant turn with full `message.usage` block → `Usage` populated correctly including cache fields.
- **test_group_stories_single_sidechain_cluster**: 1 main turn + 3 consecutive sidechain turns with linked parent_uuids → 1 `StoryRun`, `turn_count=3`, usage summed.
- **test_group_stories_two_clusters**: 1 main + 2 sidechain + 1 main + 2 sidechain → 2 `StoryRun` entries.
- **test_group_stories_with_markers_assigns_story_ids**: 2 clusters + 2 markers (timestamps just before each cluster) → story_ids match markers in order.
- **test_group_stories_marker_beyond_window_logs_warning**: marker timestamp >60s before cluster — cluster's `story_id` remains None, warning issued.
- **test_group_stories_aggregates_usage**: cluster with tokens [100/20, 50/10] → `Usage(input=150, output=30)`.
- **test_group_stories_model_is_mode**: cluster with models [\"opus\", \"opus\", \"sonnet\"] → `StoryRun.model == \"opus\"`.
- **test_summarise_computes_wall_bounds**: turns spanning 10 minutes → `BuildReport.started`/`finished` match outer timestamps.
- **test_empty_session_yields_empty_report**: JSONL with zero assistant turns → empty `stories`, zero-length duration report.