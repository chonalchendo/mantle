---
issue: 90
title: Per-command parity tests for build, implement, plan-stories
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a Mantle maintainer refactoring a top-3 prompt, I want a failing test to surface any unintended text change so I can review the diff before shipping the refactor.

## Depends On

Story 1 (parity harness foundation).

## Approach

Add one parity test per in-scope command using the `run_prompt_parity()` helper from story 1 and `inline_snapshot` to capture the baseline. Each test follows the same four-line shape — build fixture, call harness, assert matches, snapshot baseline — so the pattern is copy-pasteable for future promotions from DEFERRED to INTEGRATED.

## Implementation

### tests/parity/test_build_parity.py (new file)

```python
from __future__ import annotations

from pathlib import Path

from inline_snapshot import snapshot

from tests.parity.fixtures import build_sandbox_fixture
from tests.parity.harness import run_prompt_parity


def test_build_prompt_parity(tmp_path: Path) -> None:
    fixture = build_sandbox_fixture(tmp_path)
    result = run_prompt_parity(
        command=\"build\",
        fixture=fixture,
        baseline=snapshot(),
    )
    assert result.matches, result.diff
```

### tests/parity/test_implement_parity.py (new file)

Same shape as `test_build_parity.py`, with `command=\"implement\"`.

### tests/parity/test_plan_stories_parity.py (new file)

Same shape as `test_build_parity.py`, with `command=\"plan-stories\"`.

#### Design decisions

- **One test per file, not one parametrized test.** Parametrized snapshot tests conflate diffs when one command drifts. Separate files mean one failing snapshot doesn't hide the others, and `--inline-snapshot=review` shows each command's capture individually.
- **`assert result.matches, result.diff`.** The diff is the message. When parity fails, the pytest failure text IS the unified diff — which is what the maintainer needs to decide whether to accept via `--inline-snapshot=fix` or investigate.
- **Baseline capture workflow.** First run: `uv run pytest --inline-snapshot=create tests/parity/`. Each `snapshot()` gets filled with the current normalized prompt text. Maintainer reviews the diff, commits. Subsequent refactor: `uv run pytest tests/parity/` fails if text changed; maintainer inspects diff, then either fixes the refactor or accepts via `--inline-snapshot=fix`.

## Tests

The three files above ARE the tests — each asserts parity for one command. No separate test-of-tests needed; the harness was covered by story 1.

After story 1 lands:
1. Run `uv run pytest --inline-snapshot=create tests/parity/test_build_parity.py tests/parity/test_implement_parity.py tests/parity/test_plan_stories_parity.py`
2. Verify the three captured snapshot literals are reasonable (contain `normalize_prompt_output` sentinels where expected, do NOT contain raw timestamps / absolute paths / git SHAs)
3. Commit. Re-run `uv run pytest tests/parity/` — must pass without `--inline-snapshot=create`.