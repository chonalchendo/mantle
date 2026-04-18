---
issue: 56
title: Core hook dispatcher with env passthrough and fail-open semantics
status: in-progress
failure_log: null
tags:
- type/story
- status/in-progress
---

## User Story

As a mantle user who wants to trigger a shell script on lifecycle events
(e.g. to push status updates to Jira or Linear), I want mantle to invoke
`<mantle-dir>/hooks/on-<event>.sh` with documented positional args and
user-supplied env vars, without mantle ever importing a tracker library or
blocking when the hook fails, so that integration with any tracker stays
on the user's side of the seam.

## Depends On

None — foundation story for issue 56.

## Approach

Add a new deep module `src/mantle/core/hooks.py` that owns all hook-invocation
logic. Public interface: a single `dispatch()` function. Internals hide path
resolution, env-var loading from `config.md` frontmatter, subprocess wiring,
timeout, and fail-open error handling.

Add a `hooks_env` field to the existing `_ConfigFrontmatter` pydantic model
in `src/mantle/core/project.py` so that the field is accepted (mantle
otherwise ignores it on load). The key stays opt-in — absent `hooks_env:`
means no extra env vars.

This story only builds the dispatcher and validates its behaviour. Wiring
into actual lifecycle transitions lives in story 02.

## Implementation

### `src/mantle/core/project.py` (modify)

Extend `_ConfigFrontmatter` (≈ line 41) with a new optional field:

```python
class _ConfigFrontmatter(pydantic.BaseModel):
    """Config.md frontmatter schema (internal)."""

    personal_vault: str | None = None
    verification_strategy: str | None = None
    auto_push: bool = False
    storage_mode: str | None = None
    hooks_env: dict[str, str] | None = None
    tags: tuple[str, ...] = ("type/config",)
```

No other changes in `project.py`. The existing load/save paths validate
against this model, so a `hooks_env:` key in `.mantle/config.md` will now
round-trip cleanly.

### `src/mantle/core/hooks.py` (new)

Create the module. Structure:

```python
"""Lifecycle hook dispatch — user-supplied shell scripts.

Mantle invokes <mantle-dir>/hooks/on-<event>.sh on lifecycle events.
The seam is deliberately opaque: mantle never imports tracker libraries,
never stores credentials, and never interprets the script's exit code
beyond "success" vs "warn-and-continue".
"""

from __future__ import annotations

import logging
import os
import subprocess
from typing import TYPE_CHECKING

import yaml

from mantle.core import project

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)

HOOK_TIMEOUT_SECONDS = 30


def dispatch(
    event: str,
    *,
    issue: int,
    status: str,
    title: str,
    project_dir: Path,
) -> None:
    """Invoke the on-<event>.sh hook if present.

    Positional args passed to the script (in order):
    issue number, new status, issue title.

    Env vars exported to the script: the caller's existing env plus
    every key/value under `hooks_env:` in <mantle-dir>/config.md
    frontmatter.

    Missing script: silent no-op.
    Non-zero exit / timeout / OSError: warn-and-continue (never raises).

    Args:
        event: Event name (e.g. "issue-shaped"). Resolves to
            <mantle-dir>/hooks/on-<event>.sh.
        issue: Issue number to pass as $1.
        status: Issue status to pass as $2.
        title: Issue title to pass as $3.
        project_dir: Project directory containing .mantle/.
    """
    hooks_dir = project.resolve_mantle_dir(project_dir) / "hooks"
    script = hooks_dir / f"on-{event}.sh"
    if not script.is_file():
        return

    env = os.environ.copy()
    env.update(_load_hooks_env(project_dir))

    try:
        subprocess.run(
            [str(script), str(issue), status, title],
            env=env,
            timeout=HOOK_TIMEOUT_SECONDS,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        logger.warning(
            "Hook on-%s.sh exited %s (continuing). stderr: %s",
            event, exc.returncode, (exc.stderr or "").strip(),
        )
    except subprocess.TimeoutExpired:
        logger.warning(
            "Hook on-%s.sh timed out after %ss (continuing).",
            event, HOOK_TIMEOUT_SECONDS,
        )
    except OSError as exc:
        logger.warning(
            "Hook on-%s.sh failed to execute: %s (continuing).",
            event, exc,
        )


def _load_hooks_env(project_dir: Path) -> dict[str, str]:
    """Return the `hooks_env:` dict from config.md frontmatter, or empty.

    Reads the raw YAML frontmatter block directly rather than going
    through vault.read_note so that a malformed or missing file
    degrades silently to an empty dict (seam principle: hooks never
    block the workflow).
    """
    config_path = project.resolve_mantle_dir(project_dir) / "config.md"
    if not config_path.is_file():
        return {}
    text = config_path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    _, _, rest = text.partition("---\n")
    front, _, _ = rest.partition("\n---")
    try:
        data = yaml.safe_load(front) or {}
    except yaml.YAMLError:
        return {}
    raw = data.get("hooks_env") or {}
    if not isinstance(raw, dict):
        return {}
    return {str(k): str(v) for k, v in raw.items()}
```

**Note on the private YAML reader**: the existing `vault.read_note` path
validates the full frontmatter against `_ConfigFrontmatter`, so that path
works too. But hook dispatch must never raise — if the user has edited
`config.md` and temporarily broken validation, hook dispatch should still
proceed with an empty `hooks_env`. The private reader above makes that
graceful degradation explicit. If `_ConfigFrontmatter`-validated reads are
preferred by review, swap in `vault.read_note(config_path)` wrapped in a
try/except that falls back to `{}` — same net behaviour.

### Design decisions

- **Sync not async**: shaped doc chose sync so hook errors surface as
  warnings the user sees. Async opt-in is a future knob.
- **Timeout 30s**: shaped doc's open question. 30s covers normal curl /
  CLI round-trips with headroom; pathological stalls surface as a
  warning the user can act on.
- **`capture_output=True, text=True`**: swallow stdout/stderr by default
  to avoid polluting the mantle CLI output. Surface stderr only on
  non-zero exit (warning log message).
- **Never raise from `dispatch()`**: the fail-open contract is the whole
  point. Three except branches: `CalledProcessError`, `TimeoutExpired`,
  `OSError` (covers permission denied, ENOENT edge cases, fork failures).

## Tests

### `tests/core/test_hooks.py` (new)

Create a test module. Reuse project's `tmp_path` pattern. No LLM calls, no
network. Key scenarios:

```python
import os
import stat
from pathlib import Path

import pytest

from mantle.core import hooks, project


def _init_project(tmp_path: Path) -> Path:
    """Initialize a minimal .mantle/ for hook tests."""
    project.init_project(tmp_path)  # use existing init; fallback below
    # if init_project doesn't exist, manually create .mantle/ + config.md
    return tmp_path


def _write_hook(project_dir: Path, event: str, body: str) -> Path:
    hooks_dir = project_dir / ".mantle" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    script = hooks_dir / f"on-{event}.sh"
    script.write_text("#!/usr/bin/env bash\n" + body)
    script.chmod(script.stat().st_mode | stat.S_IXUSR)
    return script


def test_missing_script_is_silent_noop(tmp_path, caplog):
    _init_project(tmp_path)
    hooks.dispatch(
        "issue-shaped",
        issue=42, status="shaped", title="demo",
        project_dir=tmp_path,
    )
    assert caplog.records == []  # no warnings


def test_dispatch_invokes_script_with_positional_args(tmp_path):
    _init_project(tmp_path)
    marker = tmp_path / "marker.txt"
    _write_hook(
        tmp_path, "issue-shaped",
        f'echo "$1|$2|$3" > {marker}\n',
    )
    hooks.dispatch(
        "issue-shaped",
        issue=42, status="shaped", title="My Title",
        project_dir=tmp_path,
    )
    assert marker.read_text().strip() == "42|shaped|My Title"


def test_dispatch_exports_hooks_env(tmp_path):
    _init_project(tmp_path)
    # Write hooks_env into config.md frontmatter
    config = tmp_path / ".mantle" / "config.md"
    config.write_text(
        "---\n"
        "hooks_env:\n"
        "  JIRA_BASE_URL: https://example.atlassian.net\n"
        "  TEAM: platform\n"
        "tags: [type/config]\n"
        "---\n\n## Body\n"
    )
    marker = tmp_path / "env.txt"
    _write_hook(
        tmp_path, "issue-shaped",
        f'echo "$JIRA_BASE_URL|$TEAM" > {marker}\n',
    )
    hooks.dispatch(
        "issue-shaped",
        issue=1, status="shaped", title="x",
        project_dir=tmp_path,
    )
    assert marker.read_text().strip() == (
        "https://example.atlassian.net|platform"
    )


def test_non_zero_exit_warns_and_does_not_raise(tmp_path, caplog):
    _init_project(tmp_path)
    _write_hook(tmp_path, "issue-shaped", "exit 7\n")
    # Must not raise
    hooks.dispatch(
        "issue-shaped",
        issue=1, status="shaped", title="x",
        project_dir=tmp_path,
    )
    # And must have logged a warning
    assert any(
        "exited 7" in r.message and r.levelname == "WARNING"
        for r in caplog.records
    )


def test_timeout_warns_and_does_not_raise(tmp_path, caplog, monkeypatch):
    _init_project(tmp_path)
    _write_hook(tmp_path, "issue-shaped", "sleep 10\n")
    monkeypatch.setattr(hooks, "HOOK_TIMEOUT_SECONDS", 0.2)
    hooks.dispatch(
        "issue-shaped",
        issue=1, status="shaped", title="x",
        project_dir=tmp_path,
    )
    assert any(
        "timed out" in r.message and r.levelname == "WARNING"
        for r in caplog.records
    )


def test_malformed_config_degrades_to_empty_env(tmp_path):
    _init_project(tmp_path)
    config = tmp_path / ".mantle" / "config.md"
    config.write_text("---\nnot: [valid\nyaml\n---\nbody\n")
    marker = tmp_path / "env.txt"
    _write_hook(
        tmp_path, "issue-shaped",
        f'echo "${{JIRA_BASE_URL:-unset}}" > {marker}\n',
    )
    # Must not raise; must not export anything from the broken config.
    hooks.dispatch(
        "issue-shaped",
        issue=1, status="shaped", title="x",
        project_dir=tmp_path,
    )
    assert marker.read_text().strip() == "unset"
```

**Important notes for the implementer**:

- Use the project's standard init helper (`mantle init` runs through
  `project.init_project` or similar) to create `.mantle/`. If that helper
  has a different name or signature, inline a minimal setup in a test
  fixture — just `tmp_path/.mantle/` with a valid `config.md`. Look at
  `tests/core/test_project.py` for the canonical pattern.
- Tests should assert via `caplog` with `caplog.set_level(logging.WARNING,
  logger="mantle.core.hooks")` at the top of each test that inspects logs.
- `pytest.raises` should NOT appear around `hooks.dispatch()` in any test
  — the whole point is that dispatch never raises.
- Do not mock `subprocess.run` — the tests write real trivial bash
  scripts. That catches argv-order bugs unit mocks miss.

## Acceptance criteria covered by this story

- AC1 (mantle invokes `<mantle-dir>/hooks/on-<event>.sh` with documented
  positional args) — via `test_dispatch_invokes_script_with_positional_args`
- AC3 (`hooks_env:` keys exported as env vars) — via
  `test_dispatch_exports_hooks_env`
- AC4 (works for both global and per-project) — inherited via
  `project.resolve_mantle_dir()` which already handles both modes; the
  test uses per-project, but the resolver is untouched by this story.
- AC5 (missing hook no-op) — via `test_missing_script_is_silent_noop`
- AC6 (hook failure logs warning, does not block) — via
  `test_non_zero_exit_warns_and_does_not_raise` and
  `test_timeout_warns_and_does_not_raise`
- AC12 partial (covered by tests) — contributes test file for all
  dispatcher behaviour
