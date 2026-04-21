---
issue: 84
title: mantle model-tier CLI subcommand
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a Mantle user on API billing, I want a machine-readable `mantle model-tier` command that prints the resolved per-stage models as JSON, so `build.md` can consume the tier without duplicating resolution logic in the prompt.

## Depends On

Story 2 — wraps `project.load_model_tier`.

## Approach

Thin CLI wrapper following `mantle introspect-project`'s pattern (`cli/verify.py:run_introspect_project`): dump JSON to stdout for machine consumption, human-friendly summary to stderr. Registered as a top-level `@app.command` in `cli/main.py`, grouped under `GROUPS["setup"]` (same group as `introspect-project` and `where` — project-introspection commands). Keeps `cli/` thin — all logic lives in `core/project.py`.

## Implementation

### src/mantle/cli/models.py (new file)

New thin CLI wrapper module (mirrors `cli/verify.py`):

```python
"""CLI wrapper for model-tier resolution."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from rich.console import Console

from mantle.core import project

console = Console()


def run_model_tier(
    *,
    project_dir: Path | None = None,
) -> None:
    """Resolve stage→model mapping and print as JSON.

    Prints a JSON object to stdout (for machine consumption by
    build.md) and a human-readable table to stderr.

    Args:
        project_dir: Project directory. Defaults to cwd.
    """
    if project_dir is None:
        project_dir = Path.cwd()

    stages = project.load_model_tier(project_dir)
    payload = stages.model_dump()

    print(json.dumps(payload))

    print("=== Resolved model tier ===", file=sys.stderr)
    for stage, model in payload.items():
        print(f"  {stage:<14} → {model}", file=sys.stderr)
```

### src/mantle/cli/main.py (modify)

1. Add `models` to the `from mantle.cli import (...)` block (alphabetical position after `learning` / before `product_design`).
2. Register a new command between `introspect_project_command` and `transition_issue_verified_command`:

   ```python
   @app.command(name="model-tier", group=GROUPS["setup"])
   def model_tier_command(
       path: Annotated[
           Path | None,
           Parameter(
               name="--path",
               help="Project directory. Defaults to cwd.",
           ),
       ] = None,
   ) -> None:
       """Print the resolved per-stage model tier as JSON."""
       models.run_model_tier(project_dir=path)
   ```

Note: no `--json` flag — JSON is the only output format on stdout; this keeps the command unambiguous for `build.md` to consume via `$(mantle model-tier)`. Human readers still get the table on stderr.

#### Design decisions

- **Mirror introspect-project's stdout/stderr split.** JSON on stdout for machine consumption, human summary on stderr. Already proven for command-line composition in shell (`$(mantle model-tier)` returns only the JSON).
- **No --issue flag.** Model tier is a project-level resolution, not issue-scoped. Keeps the surface narrow.
- **Group under setup.** `mantle where`, `mantle introspect-project`, `mantle storage`, `mantle compile` all live there — it's the home for project-introspection helpers.
- **Thin wrapper — no CLI-side formatting logic.** All resolution logic is in `core.project.load_model_tier`. The CLI only serialises the resulting `StageModels` via `model_dump()`. Keeps the `core/ → cli/` dependency direction intact (import-linter enforced).

## Tests

### tests/cli/test_models.py (new file)

Use `cyclopts` dispatcher directly per the existing `tests/cli/test_verify.py` pattern — invoke via `app.meta` or just call the wrapper directly with a `tmp_path`.

- **test_prints_json_to_stdout**: Init a project with `init_project`, call `run_model_tier(project_dir=tmp_path)` with `capsys`, assert stdout is parseable JSON and has all 7 stage keys with string values.
- **test_json_matches_load_model_tier**: Call `run_model_tier` and `project.load_model_tier` on the same `tmp_path` and assert `json.loads(stdout) == stages.model_dump()`.
- **test_fallback_when_no_config**: Empty `tmp_path` (no `.mantle/`) → stdout JSON equals `_FALLBACK_STAGE_MODELS.model_dump()` (no crash on missing config).
- **test_override_applied_in_json**: `init_project` + `update_config(..., models={"preset": "balanced", "overrides": {"implement": "haiku"}})` → stdout JSON has `"implement": "haiku"`.
- **test_stderr_has_summary_table**: Same setup as above, assert `capsys.readouterr().err` contains `"Resolved model tier"` and at least one stage name.

Fixtures: `_mock_git` from `tests/conftest.py` if autouse (check); otherwise add per-test monkeypatching of git identity.

### tests/test_workflows.py (modify — one line)

If this file has a "CLI commands list" sanity test (pattern common in cyclopts projects), add `"model-tier"` to the expected set. If not present, skip this test file — no change needed. (Check during implementation.)
