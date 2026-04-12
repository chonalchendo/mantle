---
issue: 54
title: Build-start/build-finish CLI and implement.md wiring
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a user running `/mantle:build` or `/mantle:implement`, I want a build-report file written to `.mantle/builds/` after each run so that I can review which model was used per story, pass/fail outcomes, and relative duration without digging through session logs.

## Depends On

Story 1 (uses `core.telemetry` types and functions).

## Approach

Two new cyclopts CLI commands in `src/mantle/cli/builds.py` wrap the parser from story 1: `mantle build-start --issue N` captures the current session id + start time and writes a stub build file; `mantle build-finish --issue N` re-opens the stub, parses the JSONL via `core.telemetry`, and writes frontmatter + a rendered markdown summary. Wire into `claude/commands/mantle/implement.md` with two call sites. Follows the pattern of `cli/session.py` — thin wrapper calling pure core.

## Implementation

### src/mantle/core/telemetry.py (modify)

Add these helpers (keep them here, not in the CLI module, so the core module owns report generation):

- `current_session_id() -> str` — read `CLAUDE_SESSION_ID` environment variable. Raises `RuntimeError` with a clear message if unset (the Claude Code CLI sets it).
- `render_report(report: BuildReport, issue: int, markers: tuple[Marker, ...]) -> str` — returns the full build file body: YAML frontmatter (issue, started, finished, session_id, stories array with per-story model/tokens/duration) plus a `## Summary` markdown section with a story table.

### src/mantle/cli/builds.py (new file)

Module docstring: `\"CLI wiring for build-pipeline telemetry commands.\"`

Imports: `from __future__ import annotations`, `datetime`, `pathlib.Path`, `rich.console.Console`, `from mantle.core import project, state, telemetry`.

#### Public functions

- `run_build_start(issue: int, project_dir: Path | None = None) -> None`:
  1. Resolve project_dir (default `Path.cwd()`).
  2. `session_id = telemetry.current_session_id()`.
  3. Compute stub file: `.mantle/builds/build-{issue:02d}-{UTC YYYYMMDD-HHMM}.md`.
  4. Write stub containing only: `---\nissue: N\nstarted: <iso>\nsession_id: <id>\nstatus: in-progress\n---\n`.
  5. Record path in `.mantle/state.md`? No — instead, `build-finish` globs for the most recent `build-{issue:02d}-*.md` with `status: in-progress` and reuses it (keeps state.md untouched).
  6. Print confirmation.

- `run_build_finish(issue: int, project_dir: Path | None = None) -> None`:
  1. Find the most recent in-progress stub for this issue under `.mantle/builds/`. If none, print a warning and exit cleanly (build-start was likely skipped).
  2. Read stub frontmatter to recover `session_id` + `started`.
  3. Derive markers: scan `$project_dir/.mantle/stories/issue-{NN}-story-*.md` files — pull `story_number` and use file mtime as a proxy marker timestamp. (Better markers require orchestrator cooperation in a follow-up; mtime is good enough for v1 because the orchestrator touches each story file via `update-story-status`.)
  4. `session_file = telemetry.find_session_file(session_id)`; `turns = telemetry.read_session(session_file)`; `runs = telemetry.group_stories(turns, markers)`; `report = telemetry.summarise(session_id, turns, runs)`.
  5. Overwrite the stub with `telemetry.render_report(report, issue, markers)` appended with `finished: <iso>` and `status: complete`.
  6. Print confirmation with the path.

Handle the case where `CLAUDE_SESSION_ID` is unset (e.g., running outside Claude Code): print a clear `[yellow]Warning[/yellow]` and exit 0 — do not fail the build pipeline.

### src/mantle/cli/main.py (modify)

Add import `from mantle.cli import builds` and two `@app.command` wrappers:

```python
@app.command(name=\"build-start\")
def build_start_command(issue: Annotated[int, Parameter(name=\"--issue\")]) -> None:
    \"\"\"Record the start of a build pipeline run (writes stub telemetry file).\"\"\"
    builds.run_build_start(issue)

@app.command(name=\"build-finish\")
def build_finish_command(issue: Annotated[int, Parameter(name=\"--issue\")]) -> None:
    \"\"\"Finalize the build report by parsing Claude Code session JSONL.\"\"\"
    builds.run_build_finish(issue)
```

### claude/commands/mantle/implement.md (modify)

- Add to Step 2, immediately after `mantle transition-issue-implementing --issue {NN}`:

  `mantle build-start --issue {NN}` — and note in surrounding prose: \"Silently writes a stub build record to `.mantle/builds/`; it is safe to ignore if you are running outside Claude Code.\"

- Add to Step 6 (very start, before summarising):

  `mantle build-finish --issue {NN}` — and note: \"Finalizes the build report at `.mantle/builds/build-{NN}-<timestamp>.md`. Mention the report path in the recommendation at the end of the step.\"

### claude/commands/mantle/build.md (modify)

Step 9 summary table gains one row: `| Build report | `.mantle/builds/...` |`.

#### Design decisions

- **Stub + finalise over single write**: we need start time at spawn time but most usage data only after the run; two calls keeps concerns separate.
- **Glob-for-stub instead of state.md pointer**: state.md is already mutated enough — builds directory is a cleaner source of truth.
- **mtime markers for v1**: keeps this story small. A follow-up issue can add explicit marker capture if correlation proves flaky.
- **Graceful degradation when `CLAUDE_SESSION_ID` missing**: never block the build pipeline; always exit 0.

## Tests

### tests/core/test_telemetry.py (modify — add helpers)

- **test_current_session_id_reads_env**: monkeypatch `CLAUDE_SESSION_ID=abc` → returns `\"abc\"`.
- **test_current_session_id_missing_raises**: unset env var → `RuntimeError` with `CLAUDE_SESSION_ID` in message.
- **test_render_report_emits_yaml_frontmatter**: `BuildReport` with 2 stories → output starts with `---`, contains `issue: 54`, `stories:` list with `model` / `duration_s`, ends with `## Summary` section containing a table.
- **test_render_report_zero_stories**: empty report → still emits valid frontmatter + \"No story runs detected\" summary.

### tests/cli/test_builds.py (new file)

Use `tmp_path` for project dir, `monkeypatch` for env + home. Never touch real `~/.claude/`.

- **test_build_start_writes_stub**: call `run_build_start(54)` → `.mantle/builds/build-54-<ts>.md` exists with frontmatter (`issue: 54`, `status: in-progress`, `session_id`).
- **test_build_start_without_session_id_warns_and_exits**: env unset → no stub written, printed warning, no exception.
- **test_build_finish_parses_jsonl_and_overwrites_stub**: pre-create a stub + a fake JSONL (under `CLAUDE_PROJECTS_DIR`) with 1 main + 2 sidechain turns → after `run_build_finish(54)`, stub is overwritten with `status: complete` frontmatter and a summary section referencing 1 story.
- **test_build_finish_with_no_stub_warns_cleanly**: no prior stub → warning, exit 0, no file created.
- **test_build_finish_with_missing_session_file_warns**: stub references unknown session id → warning, stub left as-is (or marked `status: error`).
- **test_build_finish_correlates_stories_by_mtime_markers**: write two story files with different mtimes around the sidechain timestamps → resulting report's stories have correct `story_id` assigned.

### tests/test_workflows.py (modify)

- **test_implement_md_references_build_telemetry**: read `claude/commands/mantle/implement.md`, assert it contains `mantle build-start --issue` and `mantle build-finish --issue` strings.