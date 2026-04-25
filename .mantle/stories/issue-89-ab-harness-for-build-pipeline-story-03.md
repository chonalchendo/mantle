---
issue: 89
title: CLI command mantle ab-build-compare — load build files, compose artefacts,
  print report
status: in-progress
failure_log: null
tags:
- type/story
- status/in-progress
---

## User Story

As a Mantle maintainer, I want `mantle ab-build-compare <baseline.md> <candidate.md>` so I can turn two already-written build reports into a side-by-side comparison without running any builds or editing files by hand.

## Depends On

Stories 1 and 2 — consumes `project.load_prices` and the `core.ab_build` public API.

## Approach

Follow the existing thin-CLI pattern used by `cli/builds.py` (`run_build_start`, `run_build_finish`): one module under `src/mantle/cli/ab_build.py` holding a `run_ab_build_compare()` function that does the glue work (read build file frontmatter → resolve session JSONL via `telemetry.find_session_file` → parse → compose `BuildArtefacts` → call `core.ab_build.build_comparison` → print or write markdown via `rich.Console`). Register under `GROUPS["review"]` because the harness is a review-time comparison tool. Name is flat kebab-case (`ab-build-compare`) to match the rest of the CLI — no cyclopts sub-apps are currently used.

## Implementation

### src/mantle/cli/ab_build.py (new file)

- Imports: `from pathlib import Path`, `from rich.console import Console`, `from mantle.core import ab_build, issues, project, stages, stories, telemetry`. No import from `mantle.core.ab_build` that would break the existing `core` → `cli` layering (import-linter contract unchanged).

- Module-level `console = Console()` (matches `cli/builds.py`).

- `def run_ab_build_compare(baseline: Path, candidate: Path, *, output: Path | None = None, project_dir: Path | None = None) -> None`.
  - Resolves `project_dir` to `Path.cwd()` when `None`.
  - For each of `baseline`, `candidate`:
    1. Read the build file text.
    2. Extract the frontmatter using `project._read_frontmatter_and_body()` (already-tested path).
    3. Pull `issue` (int or None) and `session_id` (str) from the dict. If `session_id` is missing, print a red error `[red]Error:[/red] <path> has no session_id in frontmatter` and return (non-raising; matches `cli/builds.py` degrade-gracefully posture).
    4. Locate the session JSONL via `telemetry.find_session_file(session_id)`. On `FileNotFoundError`, print warning and skip — renderer still works with empty `report.stories`.
    5. Parse the parent session, locate sub-agent JSONLs, read the stage-marks file for this session, and call `telemetry.group_stories(parent_turns, subagent_paths, stage_windows)` to reconstruct the per-stage `StoryRun` set. Reuses the exact code path of `cli/builds.py::run_build_finish`.
    6. Build `telemetry.summarise(session_id, parent_turns, runs)` → `BuildReport`.
    7. Load the issue note + story notes via `issues.load_issue` / `stories.list_stories` + `stories.load_story` (ignore `FileNotFoundError` — harness tolerates missing quality data by passing `None` / empty tuple into `ab_build.BuildArtefacts`).
    8. Construct a `BuildArtefacts(label=baseline.stem, issue=issue, report=report, issue_note=issue_note, stories=tuple(story_notes))`.
  - Call `project.load_prices(project_dir)` once. On `FileNotFoundError` or `KeyError`, print a red error explaining the missing `prices:` block and return.
  - Call `ab_build.build_comparison(baseline_art, candidate_art, prices)` → `Comparison`.
  - Call `ab_build.render_markdown(comparison)` → string.
  - If `output` is set, write to that file via `output.write_text(rendered, encoding="utf-8")` and log `[green]Report written:[/green] {output}`. Otherwise print the rendered string to stdout via `console.print(rendered)`.

### src/mantle/cli/main.py (modify)

Register one new command at a sensible line-grouping (adjacent to the existing `build-start` / `build-finish` commands or the review group — use `GROUPS["review"]`):

```python
@app.command(name="ab-build-compare", group=GROUPS["review"])
def ab_build_compare_command(
    baseline: Annotated[
        Path,
        Parameter(
            name="--baseline",
            help="Path to the baseline build report (in .mantle/builds/).",
        ),
    ],
    candidate: Annotated[
        Path,
        Parameter(
            name="--candidate",
            help="Path to the candidate build report (in .mantle/builds/).",
        ),
    ],
    output: Annotated[
        Path | None,
        Parameter(
            name="--output",
            help="Optional path to write the rendered report. Prints to stdout when unset.",
        ),
    ] = None,
    path: Annotated[
        Path | None,
        Parameter(
            name="--path",
            help="Project directory. Defaults to cwd.",
        ),
    ] = None,
) -> None:
    """Compare two already-written build reports and print an A/B report."""
    ab_build_cli.run_ab_build_compare(
        baseline=baseline,
        candidate=candidate,
        output=output,
        project_dir=path,
    )
```

Add `ab_build as ab_build_cli` to the module import list at the top of `main.py` (use an alias to avoid shadowing `mantle.core.ab_build` if ever imported in the same scope).

#### Design decisions

- **Flat kebab-case name `ab-build-compare`**: matches the existing CLI shape (every command on `mantle --help` is flat). Avoids introducing a cyclopts sub-app pattern solely for one new command.
- **Degrade-gracefully on missing session JSONL**: the harness must still produce a report for two old build files whose sessions have since been cleaned up — `group_stories` naturally returns empty when given empty inputs, and `render_markdown` is designed to emit legitimate zeros.
- **Hard-error on missing `prices:` block**: this is the one failure mode where the report would be structurally wrong (all cost values zero). A clear error beats a misleading report.
- **`GROUPS["review"]`**: semantically the harness is a review-time tool, not an implementation step.

## Tests

### tests/cli/test_ab_build.py (new file)

Each test builds a self-contained `tmp_path` fixture: a fake `.mantle/` tree with `.mantle/cost-policy.md` (containing a `prices:` block), a fake Claude projects directory (set via `monkeypatch.setenv("CLAUDE_PROJECTS_DIR", str(tmp_path / "projects"))`), and two minimal build-file stubs whose frontmatter carries a known `session_id`, plus matching JSONL session files. Follow the pattern in `tests/core/test_telemetry.py` and `tests/cli/test_stage_begin.py` for fixture construction.

- **test_run_ab_build_compare_prints_report_to_stdout**: invoke `main.ab_build_compare_command(baseline=..., candidate=..., path=tmp_path)` with two real fixture build files that each point at a tiny synthetic JSONL session. Assert the captured stdout contains the markdown header `# A/B build comparison` and at least one stage subsection, and does not contain any of the sentinel substrings `<fill>`, `TBD`, `pending`, `<x>`, `<y>`. Use `capsys` to capture rich output.
- **test_run_ab_build_compare_writes_to_output_path**: same fixture, but pass `output=tmp_path / "compare.md"`; assert the file exists, contents match what would have been printed, and stdout has the `Report written:` log line.
- **test_run_ab_build_compare_errors_on_missing_session_id**: baseline build file has no `session_id` frontmatter field; assert the command returns without raising and stdout contains an `Error:` line mentioning `session_id`.
- **test_run_ab_build_compare_errors_on_missing_prices_block**: `.mantle/cost-policy.md` lacks the `prices:` key; assert a red error line mentioning `prices` is printed and no report is written.
- **test_run_ab_build_compare_renders_unattributed_bucket**: fixture JSONLs contain one sub-agent with a known `agentType` (mapping to `implement`) and one parent-stage window marked as `shape`; render output contains a `## Cost — shape` subsection, a `## Cost — implement` subsection, and no `Unattributed` subsection. Then add a second fixture with a sub-agent whose `meta.json` is missing (`stage=None`); assert the `Unattributed` bucket appears.
- **test_ab_build_compare_command_registered_in_review_group**: call `main.app.help_()` or inspect `main.app` to assert the command is registered under `GROUPS["review"]` (consistent with taxonomy test in `tests/cli/test_help_groups.py`).

Fixture notes:
- Minimal JSONL session for each build: two assistant turns with `usage` blocks to exercise the real `telemetry.read_session` path.
- Minimal `.meta.json` sidecar to exercise `stage` attribution.
- Use `inline_snapshot` for the full rendered comparison when the test is deterministic. Use `dirty-equals` for assertions on numeric fields that depend on wall-clock timestamps.