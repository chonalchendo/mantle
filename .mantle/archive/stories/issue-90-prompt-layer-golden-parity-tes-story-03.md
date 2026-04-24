---
issue: 90
title: Prompt coverage policy test and CLAUDE.md parity-harness docs
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a Mantle contributor adding a new `/mantle:*` command, I want CI to force me to make an explicit decision about parity coverage rather than silently skip it; and as a maintainer, I want a short playbook for capturing and promoting baselines.

## Depends On

None — independent of stories 1 and 2. Touches `tests/parity/test_prompt_coverage_policy.py` and `CLAUDE.md` only.

## Approach

Add a single policy test that enumerates every `/mantle:*` command file on disk and asserts each is present in a `_CLASSIFICATIONS` dict with one of three values — `INTEGRATED`, `UNIT_ONLY`, or `DEFERRED` — plus a one-line rationale. Mirror GSD's `golden-policy.test.ts`. Pair with a short section in `CLAUDE.md` under Test Conventions explaining the capture-and-promote workflow.

## Implementation

### tests/parity/test_prompt_coverage_policy.py (new file)

```python
from __future__ import annotations

from pathlib import Path

import pytest

# Classifications:
# - INTEGRATED: a parity test exists under tests/parity/test_<cmd>_parity.py.
# - UNIT_ONLY: covered by unit tests in tests/core/ or tests/cli/; no parity test needed.
# - DEFERRED: not currently covered; add a parity test when refactor pressure rises.
#
# Every value is a pair (classification, rationale). Rationale is a one-liner
# that explains WHY, not WHAT — readers should understand the trade-off.
_CLASSIFICATIONS: dict[str, tuple[str, str]] = {
    # INTEGRATED
    \"build\": (\"INTEGRATED\", \"top-3 token cost; direct refactor target for issues 79/87/88.\"),
    \"implement\": (\"INTEGRATED\", \"top-3 token cost; direct refactor target for issues 79/87/88.\"),
    \"plan-stories\": (\"INTEGRATED\", \"top-3 token cost; direct refactor target for issues 79/87/88.\"),
    # DEFERRED — add the rest at import time (see _collect_all_commands)
}

_DEFAULT_DEFERRED_RATIONALE = (
    \"low refactor pressure; promote to INTEGRATED if it joins the token-cut queue.\"
)


def _commands_dir() -> Path:
    # claude/commands/mantle lives at the repo root during development.
    return Path(__file__).resolve().parents[2] / \"claude\" / \"commands\" / \"mantle\"


def _collect_all_commands() -> set[str]:
    d = _commands_dir()
    names: set[str] = set()
    for p in d.iterdir():
        if p.suffix == \".md\":
            names.add(p.stem)
        elif p.name.endswith(\".md.j2\"):
            names.add(p.name.removesuffix(\".md.j2\"))
    return names


def test_every_command_has_classification() -> None:
    on_disk = _collect_all_commands()
    missing = on_disk - _CLASSIFICATIONS.keys()
    assert not missing, (
        f\"Add these commands to _CLASSIFICATIONS in \"
        f\"tests/parity/test_prompt_coverage_policy.py: {sorted(missing)}. \"
        f\"Pick INTEGRATED (write a parity test), UNIT_ONLY (cite the test), \"
        f\"or DEFERRED (one-line rationale).\"
    )


def test_no_orphan_classifications() -> None:
    on_disk = _collect_all_commands()
    orphans = _CLASSIFICATIONS.keys() - on_disk
    assert not orphans, (
        f\"Remove these stale entries from _CLASSIFICATIONS — the command files \"
        f\"no longer exist: {sorted(orphans)}.\"
    )


@pytest.mark.parametrize(\"classification_value\", list(_CLASSIFICATIONS.values()))
def test_classification_values_are_valid(classification_value: tuple[str, str]) -> None:
    label, rationale = classification_value
    assert label in {\"INTEGRATED\", \"UNIT_ONLY\", \"DEFERRED\"}, (
        f\"Invalid classification label {label!r}; must be INTEGRATED, UNIT_ONLY, or DEFERRED.\"
    )
    assert rationale.strip(), \"Classification rationale must be non-empty.\"
```

After writing the test, populate `_CLASSIFICATIONS` with every remaining `/mantle:*` command mapped to `(\"DEFERRED\", _DEFAULT_DEFERRED_RATIONALE)`. Commands to enumerate are whatever `ls claude/commands/mantle/` shows at implementation time (do not hardcode a list guessed from memory — read the directory first).

#### Design decisions

- **Two-way integrity.** Both `missing` (on-disk not in dict) and `orphans` (in dict not on-disk) are asserted. This catches both \"added a command without classifying\" AND \"removed a command without cleaning up\".
- **Parametrized validity check.** Makes the validity constraint enforced per entry, so the failing entry is named in the test id.
- **Default rationale for DEFERRED bulk entries.** Keeps the dict readable. Maintainers override the default when a command has specific rationale (e.g., \"blocked by pending refactor in issue 79\").
- **No rationale for INTEGRATED needed beyond \"parity test exists\".** The pattern ``INTEGRATED → tests/parity/test_<cmd>_parity.py`` is uniform; the rationale field documents trade-off, not location.

### CLAUDE.md (modify)

Add a new subsection under `## Test Conventions`:

```markdown
### Prompt-parity harness (`tests/parity/`)

A parity test captures the normalized text of a ``/mantle:*`` command prompt
and fails if that text changes between runs. The harness enables aggressive
token-cut refactors without silently shifting agent-visible content.

- **Scope.** Three commands are `INTEGRATED`: ``build``, ``implement``, ``plan-stories``.
  Every other command has a classification in
  ``tests/parity/test_prompt_coverage_policy.py``. Adding a new command without
  a classification fails CI.
- **Capturing a new baseline.** Run
  ``uv run pytest --inline-snapshot=create tests/parity/test_<cmd>_parity.py``.
  Review the captured literal, confirm it contains no volatile fields (timestamps,
  session IDs, absolute paths, git SHAs — see ``normalize_prompt_output``), and commit.
- **Accepting a diff.** After a deliberate refactor, run
  ``uv run pytest --inline-snapshot=review tests/parity/`` and accept each diff
  interactively. Never hand-edit a ``snapshot()`` literal.
- **Promoting DEFERRED → INTEGRATED.** Copy one of the three ``test_<cmd>_parity.py``
  files, change the ``command=`` argument, capture the baseline, and flip the
  classification entry.
```

#### Design decisions

- **Inline-snapshot workflow documented at the project level.** Future maintainers shouldn't need to re-derive the create / review / fix cycle.
- **\"Volatile fields\" named explicitly.** Matches the four classes in `normalize_prompt_output` so the doc stays one grep away from the code.

## Tests

### tests/parity/test_prompt_coverage_policy.py (same file)

The three functions above ARE the tests for this story. Each asserts one invariant on the policy registry.

No new conftest fixtures; everything needed is stdlib.