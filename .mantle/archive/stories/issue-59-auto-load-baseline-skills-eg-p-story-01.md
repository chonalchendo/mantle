---
issue: 59
title: core/baseline.py — resolve baseline skills from pyproject.toml
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a Mantle contributor working on a Python 3.14+ project, I want a baseline-skills resolver that reads my project manifest so baseline language/runtime skills can be auto-included independent of issue body matching.

## Depends On

None — independent.

## Approach

New module `core/baseline.py` with a pure version-band mapping function and a resolver that reads `pyproject.toml` via `tomllib` (3.14 stdlib). Follows the same single-responsibility pattern as `core/freshness.py` and `core/patterns.py`: small, focused, unit-testable. Soft-fails on missing manifest, missing vault config, or unrecognised version — baselines are additive, never a failure surface.

## Implementation

### src/mantle/core/baseline.py (new file)

Create a new module exposing two functions:

```python
"""Resolve baseline skills from project-level constraints."""

from __future__ import annotations

import tomllib
import warnings
from pathlib import Path

from mantle.core import skills


def _python_baseline_for_version(requires_python: str) -> tuple[str, ...]:
    """Map a requires-python spec to baseline skill names.

    Pure function — no filesystem access. Handles specifiers like
    ">=3.14", "~=3.14", ">=3.14,<4", "3.14.*". Returns empty tuple
    for unparseable or pre-3.14 specs.

    Args:
        requires_python: Value of pyproject.toml requires-python.

    Returns:
        Tuple of baseline skill names for the detected version.
    """
    # Extract major.minor from the first numeric token; parse robustly.
    # For >=3.14, ~=3.14, 3.14.*, etc. -> band "3.14"
    # For <3.14 or pre-3.14 lower bound, return ()
    # Return ("python-314",) when major=3 and minor>=14.


def resolve_baseline_skills(project_dir: Path) -> tuple[str, ...]:
    """Return vault-present baseline skills for the projects constraints.

    Reads project_dir/pyproject.toml, parses requires-python, maps to
    baseline skill names via _python_baseline_for_version, then filters
    to skills that actually exist in the personal vault. Emits a warning
    for each baseline skill that is missing from the vault but continues
    without failing.

    Args:
        project_dir: Directory containing pyproject.toml.

    Returns:
        Tuple of vault-present baseline skill names. Empty on any
        failure path (no pyproject, unreadable TOML, vault not
        configured, unrecognised version).
    """
    pyproject = project_dir / "pyproject.toml"
    if not pyproject.is_file():
        return ()
    try:
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError, OSError:
        return ()
    requires_python = data.get("project", {}).get("requires-python", "")
    if not requires_python:
        return ()
    candidates = _python_baseline_for_version(requires_python)
    if not candidates:
        return ()
    # Vault-presence gate; swallow VaultNotConfiguredError
    try:
        present = []
        for name in candidates:
            if skills.skill_exists(project_dir, name):
                present.append(name)
            else:
                warnings.warn(
                    f"Baseline skill \"{name}\" not found in vault — skipping.",
                    stacklevel=2,
                )
        return tuple(present)
    except skills.VaultNotConfiguredError:
        return ()
```

#### Design decisions

- **tomllib over a third-party TOML parser**: the project already targets 3.14+; tomllib is stdlib. Matches python-314 skill guidance.
- **Pure mapping function separated from IO**: `_python_baseline_for_version` takes a string and returns a tuple — trivially unit-testable without fixtures.
- **Soft failure on missing vault skill**: emits `warnings.warn` and continues. Matches the existing pattern in `skills.compile_skills` (see `src/mantle/core/skills.py:1024`).
- **Empty tuple on any failure**: the caller should not need try/except around baseline resolution.
- **Use `skills.skill_exists`, not a direct filesystem check**: respects the existing vault abstraction.
- **PEP 758 bare-except comma**: `except tomllib.TOMLDecodeError, OSError:` is valid in 3.14 — do not parenthesise.

### tests/core/test_baseline.py (new file)

Cover both the pure mapping and the resolver.

## Tests

### tests/core/test_baseline.py (new file)

Pure mapping (`_python_baseline_for_version`):

- **test_py314_lower_bound**: `">=3.14"` returns `("python-314",)`.
- **test_py315_lower_bound**: `">=3.15"` returns `("python-314",)` (band rolls forward, python-314 still the baseline unless a later skill is added).
- **test_py313_returns_empty**: `">=3.13"` returns `()`.
- **test_compatible_release**: `"~=3.14"` returns `("python-314",)`.
- **test_wildcard**: `"3.14.*"` returns `("python-314",)`.
- **test_unparseable_returns_empty**: `"garbage"` returns `()`.
- **test_empty_returns_empty**: `""` returns `()`.

Resolver (`resolve_baseline_skills`):

- **test_no_pyproject**: `tmp_path` without pyproject.toml returns `()`.
- **test_pyproject_without_requires_python**: pyproject missing `project.requires-python` returns `()`.
- **test_malformed_toml**: invalid TOML returns `()` (no exception).
- **test_py314_with_vault_skill**: pyproject says `">=3.14"`, vault has `python-314` → returns `("python-314",)`.
- **test_py314_without_vault_skill**: pyproject says `">=3.14"`, vault lacks `python-314` → returns `()` and emits a warning (use `pytest.warns`).
- **test_vault_not_configured**: pyproject says `">=3.14"`, no personal_vault in config → returns `()`, no exception.
- **test_py313_ignored_even_if_vault_has_skill**: pyproject says `">=3.13"` returns `()` regardless of vault contents.

Fixture requirements: use `tmp_path`, write a minimal `pyproject.toml`, write a minimal `.mantle/config.md` with `personal_vault: <tmp_path>/vault`, and create vault skills via the existing `skills.create_skill` helper (mirror the pattern already used in `tests/core/test_skills.py`).