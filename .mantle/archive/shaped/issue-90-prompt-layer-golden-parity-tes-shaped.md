---
issue: 90
title: Prompt-layer golden-parity test harness for top commands
approaches:
- A — Subprocess dual-run (GSD-exact)
- B — In-process direct-call harness with inline_snapshot baselines
- C — Pure snapshot on static files only
chosen_approach: B — In-process direct-call harness with inline_snapshot baselines
appetite: small batch
open_questions: []
author: 110059232+chonalchendo@users.noreply.github.com
created: '2026-04-24'
updated: '2026-04-24'
updated_by: 110059232+chonalchendo@users.noreply.github.com
tags:
- type/shaped
- phase/shaping
---

## Context

Mantle has no regression safety net at the prompt layer. The upcoming token-cut refactors (79: @file includes + audit-context CLI, 87: mantle compress, 88: audit-tokens follow-on cuts) will rewrite the highest-cost prompts. Without a parity harness, every cut is a leap of faith.

GSD solves this with `read-only-parity.integration.test.ts` + `golden-policy.test.ts` + `mutation-sandbox.ts`: dual-subprocess runs on a sandbox fixture, stripped of volatile fields, compared to baselines. A separate policy test enumerates every command and forces an explicit classification.

Scope is deliberately tight: 3 commands (`build`, `implement`, `plan-stories`) + an exception registry. GSD has this across 103 commands; Mantle has ~25 and only needs coverage on the top 3.

## Skills loaded

- `dirty-equals` — structural / partial-equality matchers for tolerating non-deterministic fields inside otherwise-snapshotted structures. Not expected to be heavily used in this shape (prompts are whole-text comparisons, not partial-dict comparisons), but available if normalizer misses a volatile field.
- `inline-snapshot` — baseline-as-capture pattern. Every parity test records its baseline inline via `snapshot()`, populated by `--inline-snapshot=create`. Anti-patterns: never hand-edit snapshot literals; never snapshot non-deterministic output without redaction.

## Relevant learnings

- Issue 74 (token-cost audit): measurement-centric issues need instrument smoke-test at shape time. For this issue: the "instrument" is the parity harness itself. I verified `mantle compile` takes a `--path` arg and renders templates in-process.
- Issue 80 (flip-ac): CLI-parse coverage gap — tests that bypass cyclopts miss binding bugs. Not directly applicable here (we're testing prompts, not CLI wiring), but a reminder that the policy test should be exhaustive.
- Issue 91 (session-start hook): lifecycle-environment verification gaps deserve explicit DONE_WITH_CONCERNS framing at shape time. None apply here — parity tests run purely in-process.

## Approaches considered

### A — Subprocess dual-run (GSD-exact)

Shell out to `mantle compile --path <fixture> --target <tmp>` as a subprocess; capture compiled prompt text; normalize; compare to baseline file.

- Appetite: medium batch (~2-3 days)
- Pros: closest to GSD pattern; exercises the full CLI wire
- Cons: over-engineered for 3 commands (only `resume.md.j2` and `status.md.j2` are j2-compiled — the other commands are static markdown); subprocess flakiness in CI; baseline files proliferate

### B — In-process direct-call harness with inline_snapshot baselines (chosen)

Call `mantle.core.compiler.compile()` directly in-process for j2 commands; read raw prompt files for static commands. Normalize in-process. Baselines stored as `inline_snapshot` literals inside each parity test.

- Appetite: small batch (~1-2 days)
- Pros: in-process tests are fast and deterministic; inline_snapshot is already the project convention; no subprocess/file baseline fanout; policy test is a trivial enumeration
- Cons: doesn't exercise the CLI subprocess wire (covered elsewhere by `tests/test_workflows.py`)

### C — Pure snapshot on static files, no helper

For each in-scope command: `assert file.read_text() == snapshot(...)`. No harness helper, no normalizer.

- Appetite: half-day
- Pros: trivial
- Cons: fails ac-01 (no `run_prompt_parity()` helper exists) and ac-03 (no `normalize_prompt_output()` helper); the helper is load-bearing for 79/87/88 when those refactors introduce @file includes that expand dynamically

## Why B

B is the smallest-appetite shape that satisfies all 7 ACs. A is over-engineered for current surface area; C fails ac-01/ac-03. B matches Mantle's existing test conventions (inline_snapshot, tmp_path fixtures, mirror-directory testing) and keeps the new code fully inside `tests/` — no `src/mantle/` surface changes. When 79/87/88 land, the same harness can be pointed at their changed prompts with no refactoring of the helper itself.

## Code design

### Strategy

New test sub-package at `tests/parity/`, structured as follows:

```
tests/parity/
  __init__.py
  harness.py              # run_prompt_parity, normalize_prompt_output, ParityResult
  fixtures.py             # build_sandbox_fixture() factory
  test_build_parity.py
  test_implement_parity.py
  test_plan_stories_parity.py
  test_prompt_coverage_policy.py
```

**Public API (`tests/parity/harness.py`):**

```python
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class ParityResult:
    \"\"\"Structured outcome of a prompt-parity comparison.\"\"\"
    command: str
    baseline_text: str
    current_text: str
    matches: bool
    diff: str  # unified diff, empty when matches=True

def run_prompt_parity(
    command: str,
    fixture: Path,
    baseline: str,
) -> ParityResult:
    \"\"\"Render `command` against `fixture`, normalize, compare to `baseline`.

    For j2-compiled commands (status, resume), uses mantle.core.compiler.compile()
    in-process. For static commands, reads the raw prompt file. The returned
    ParityResult is asserted against a snapshot() literal in the test.
    \"\"\"

def normalize_prompt_output(text: str) -> str:
    \"\"\"Strip timestamps, session IDs, absolute paths, and git SHAs.

    Replaces:
    - ISO timestamps (e.g., 2026-04-24T12:32:00Z) -> <TIMESTAMP>
    - Session UUIDs (8-4-4-4-12 hex) -> <SESSION_ID>
    - Absolute paths (/Users/..., /home/...) -> <PATH>
    - Git SHAs (7-40 hex chars, bounded by word boundaries) -> <GIT_SHA>
    \"\"\"
```

**Coverage policy (`tests/parity/test_prompt_coverage_policy.py`):**

```python
_CLASSIFICATIONS: dict[str, str] = {
    # INTEGRATED — parity test exists for this command
    \"build\": \"INTEGRATED\",
    \"implement\": \"INTEGRATED\",
    \"plan-stories\": \"INTEGRATED\",
    # DEFERRED — not yet covered; promote as regression risk rises
    \"shape-issue\": \"DEFERRED (low refactor pressure)\",
    \"verify\": \"DEFERRED (low refactor pressure)\",
    # ... one entry per command file in claude/commands/mantle/*.md
}

def test_every_command_has_classification():
    cmd_files = sorted(
        Path(\"claude/commands/mantle\").glob(\"*.md\")
    )
    cmd_names = {p.stem for p in cmd_files} | {
        p.stem.removesuffix(\".md\") for p in Path(\"claude/commands/mantle\").glob(\"*.md.j2\")
    }
    missing = cmd_names - _CLASSIFICATIONS.keys()
    assert not missing, (
        f\"Add these commands to _CLASSIFICATIONS in test_prompt_coverage_policy.py: \"
        f\"{sorted(missing)}\"
    )
```

**Fixture factory (`tests/parity/fixtures.py`):**

```python
def build_sandbox_fixture(tmp_path: Path) -> Path:
    \"\"\"Create a minimal .mantle/ tree with deterministic state.

    Writes a fixed state.md, an issue file, and a session file with
    stable (non-timestamp) IDs. Returns the project root tmp_path.
    \"\"\"
```

**Per-command test (e.g., `test_build_parity.py`):**

```python
from inline_snapshot import snapshot
from tests.parity.harness import run_prompt_parity
from tests.parity.fixtures import build_sandbox_fixture

def test_build_prompt_parity(tmp_path):
    fixture = build_sandbox_fixture(tmp_path)
    result = run_prompt_parity(command=\"build\", fixture=fixture, baseline=snapshot())
    assert result.matches, result.diff
```

Baseline is captured by running `uv run pytest --inline-snapshot=create tests/parity/`.

### Fits architecture by

- Lives entirely under `tests/` — no `src/mantle/` changes, so the import-linter contract `core/ does not import cli/` remains untouched.
- Uses `mantle.core.compiler.compile()` as a public API (already used by existing tests in `tests/core/test_compiler.py`).
- Follows project test conventions from CLAUDE.md: pytest, `tmp_path`, `inline_snapshot`, named scenario fixtures (`build_sandbox_fixture` = one named scenario).
- ac-05 (CI) auto-satisfied: `just check` runs `uv run pytest`, which picks up `tests/parity/` because of the default test discovery pattern.
- ac-06 (doc) lands as a new section in CLAUDE.md under \"Test Conventions\" — \"Prompt-parity harness: how to capture a baseline, how to promote a DEFERRED command to INTEGRATED\".

### Does not

- Does not capture agent behavior. Agent runs are non-deterministic; the harness captures prompt *text*, not agent output.
- Does not run commands through a real subprocess. In-process `compile()` calls are faster and deterministic; subprocess coverage is already provided by `tests/test_workflows.py` and `tests/test_global_mode_workflow.py`.
- Does not validate prompt correctness — only equivalence to a frozen baseline. Baseline captures what is, not what should be.
- Does not cover all ~25 commands. Initial coverage is 3 (`build`, `implement`, `plan-stories`); rest are classified `DEFERRED` with a one-line rationale.
- Does not wire into `mantle audit-tokens` or any CLI surface. It is a pure test harness.
- Does not add runtime dependencies. `inline-snapshot` and `dirty-equals` are already in `[dependency-groups.check]`.
- Does not handle normalization edge cases beyond the four fields in ac-03 (timestamps, session IDs, absolute paths, git SHAs). Additional volatile fields get added to the normalizer when the first false-positive surfaces.

## Side-effect impact scan

No state mutations in the runtime code path. The parity tests read:
- `claude/commands/mantle/*.md` (static prompt files)
- `claude/commands/mantle/*.md.j2` (via `mantle.core.compiler.compile` on a tmp fixture)

No command invocation ordering concerns — the harness is pure-read.