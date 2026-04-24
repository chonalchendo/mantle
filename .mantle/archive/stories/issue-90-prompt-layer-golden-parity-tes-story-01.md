---
issue: 90
title: 'Parity harness foundation: run_prompt_parity, normalize_prompt_output, sandbox
  fixture'
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a Mantle maintainer aggressively cutting tokens from top commands, I want a reusable parity helper and fixture factory so that parity tests across multiple commands stay consistent and small.

## Depends On

None — independent.

## Approach

Create a new `tests/parity/` sub-package containing the shared `run_prompt_parity()` helper, a `normalize_prompt_output()` normalizer that strips four classes of volatile fields, a `ParityResult` dataclass, and a `build_sandbox_fixture()` factory that writes a deterministic `.mantle/` tree. Follows the `tests/core/` mirror-directory convention from CLAUDE.md and the inline-snapshot + tmp_path conventions; no runtime dependencies are added.

## Implementation

### tests/parity/__init__.py (new file)

Empty module marker. One-line docstring only.

### tests/parity/harness.py (new file)

Public API:

```python
from __future__ import annotations

import difflib
import re
from dataclasses import dataclass
from pathlib import Path

from mantle.core import compiler


@dataclass(frozen=True)
class ParityResult:
    \"\"\"Structured outcome of a prompt-parity comparison.\"\"\"
    command: str
    baseline_text: str
    current_text: str
    matches: bool
    diff: str


def normalize_prompt_output(text: str) -> str:
    \"\"\"Strip volatile fields from a prompt-layer text capture.

    Replaces, in order:
    - ISO-8601 timestamps (e.g., ``2026-04-24T12:32:00Z``) with ``<TIMESTAMP>``
    - ISO-8601 dates (``2026-04-24``) with ``<DATE>``
    - Session UUIDs (8-4-4-4-12 hex) with ``<SESSION_ID>``
    - Absolute POSIX paths (``/Users/...``, ``/home/...``, ``/tmp/...``) with ``<PATH>``
    - Git SHAs (7-40 lowercase hex, bounded by word boundaries) with ``<GIT_SHA>``
    \"\"\"
    # Order matters: timestamp must come before date so the date inside the
    # timestamp isn't matched first.


def run_prompt_parity(
    command: str,
    fixture: Path,
    baseline: str,
) -> ParityResult:
    \"\"\"Render ``command`` against ``fixture``, normalize, compare to ``baseline``.

    For static commands (any ``claude/commands/mantle/<command>.md`` that is
    not a Jinja template), reads the raw prompt file. For j2-compiled commands
    (``resume``, ``status``), runs ``mantle.core.compiler.compile()`` in-process
    against the fixture and reads the rendered output.

    Returns a ``ParityResult`` with a unified ``difflib.unified_diff`` on mismatch.
    \"\"\"
```

Implementation notes:
- Use `re.sub` with compiled patterns for normalization. Inline the patterns as module-level constants so the regex isn't rebuilt per call.
- `run_prompt_parity` locates `claude/commands/mantle/` via `compiler.template_dir().parent` (the directory that holds both `.md` and `.md.j2` files).
- Static command detection: if `<command>.md.j2` exists, treat as j2 (compile); else read `<command>.md` raw.
- The baseline is `normalize_prompt_output(baseline)` — callers should normalize both sides so snapshot literals store the stable form.
- Use `difflib.unified_diff` joined with `\"\"`. On match, `diff` is `\"\"`.

### tests/parity/fixtures.py (new file)

```python
def build_sandbox_fixture(tmp_path: Path) -> Path:
    \"\"\"Create a minimal, deterministic .mantle/ tree.

    Named scenario fixture: \"sandbox with one planned issue and a static session\".
    Writes:
    - ``.mantle/state.md`` — frontmatter with project=\"sandbox\", status=\"planning\", stable created/updated dates
    - ``.mantle/issues/issue-01-example.md`` — a single planned issue with 2 ACs
    - ``.mantle/sessions/2026-01-01-session.md`` — one stable session file

    Returns ``tmp_path`` (the project root containing ``.mantle/``).
    \"\"\"
```

Build by calling into the public APIs of `mantle.core.issues`, `mantle.core.vault`, and direct file writes for the session/state. Deterministic values only — no `datetime.now()` calls.

#### Design decisions

- **No subprocess.** All operations are in-process against `mantle.core.compiler` and direct file reads. Subprocess coverage already exists in `tests/test_workflows.py`.
- **No baseline files on disk.** Baselines are captured via `inline_snapshot` literals inside each per-command test (story 2). This keeps each test self-contained.
- **Static vs j2 detection is path-based, not configuration-based.** Listing which commands are j2 would be a second source of truth that drifts.
- **Normalizer regexes inline.** Four classes are enough per ac-03; additional classes are added only when the first false-positive surfaces.

### tests/parity/test_harness.py (new file)

Self-tests for the harness and normalizer. Does not exercise any real prompt — just verifies the mechanisms.

## Tests

### tests/parity/test_harness.py (new file)

- **test_normalize_replaces_iso_timestamp**: input with `2026-04-24T12:32:00Z` → `<TIMESTAMP>`
- **test_normalize_replaces_iso_date**: input with `2026-04-24` (no time) → `<DATE>`
- **test_normalize_replaces_session_uuid**: input with `550e8400-e29b-41d4-a716-446655440000` → `<SESSION_ID>`
- **test_normalize_replaces_absolute_path**: input with `/Users/foo/bar` → `<PATH>`, input with `/tmp/x` → `<PATH>`
- **test_normalize_replaces_git_sha**: input with `a1b2c3d` and `a1b2c3d4e5f6789012345678901234567890abcd` → `<GIT_SHA>`
- **test_normalize_preserves_non_volatile_text**: sentence with prose and code identifiers stays unchanged
- **test_parity_result_dataclass_is_frozen**: attempting `result.matches = False` raises
- **test_run_prompt_parity_static_command_matches**: call `run_prompt_parity(\"build\", fixture, baseline=<exact normalized build.md content>)`; `result.matches is True`, `result.diff == \"\"`
- **test_run_prompt_parity_static_command_mismatch**: call with mutated baseline; `result.matches is False`, `result.diff` contains `unified diff` markers (`---`, `+++`, `@@`)
- **test_run_prompt_parity_j2_command_renders_fixture**: call `run_prompt_parity(\"status\", fixture, baseline=<normalized rendered status.md>)`; passes after `--inline-snapshot=create`. Use `inline_snapshot` here to capture the normalized j2 output.
- **test_build_sandbox_fixture_creates_mantle_tree**: `build_sandbox_fixture(tmp_path)` returns `tmp_path`; `(tmp_path / \".mantle\" / \"state.md\").exists()`; state frontmatter has `project: sandbox` and `status: planning`.

Test fixture: `tmp_path` only — no shared fixtures in `conftest.py` yet (scope stays in this story).