---
issue: 56
title: Wire hooks.dispatch into shaping + 4 issue transitions
status: planned
failure_log: null
tags:
- type/story
- status/planned
---

## User Story

As a mantle user running `/mantle:shape-issue`, `/mantle:verify`,
`/mantle:review`, or `/mantle:implement`, I want each successful lifecycle
transition to invoke the corresponding `on-<event>.sh` hook automatically,
so that my shipped example scripts push status updates to my tracker without
extra commands.

## Depends On

Story 01 (core hook dispatcher).

## Approach

Wire `hooks.dispatch()` into the four lifecycle transition points plus the
shaping save. The call-sites live in `core/issues.py` and `core/shaping.py`.
The event-to-function mapping is fixed and exhaustive (from the shaped doc's
table):

| Event | Call-site function |
|---|---|
| `issue-shaped` | `core/shaping.py::save_shaped_issue` |
| `issue-implement-start` | `core/issues.py::transition_to_implementing` |
| `issue-verify-done` | `core/issues.py::transition_to_verified` |
| `issue-review-approved` | `core/issues.py::transition_to_approved` |

Each call-site dispatches after the existing write/state-update succeeds —
so a failed transition does not fire a hook. The dispatch is fire-and-forget
from the caller's perspective: dispatch never raises, so there's no error
handling at the call-site.

## Implementation

### `src/mantle/core/issues.py` (modify)

Import the new module at the top:

```python
from mantle.core import hooks, project, state, vault
```

In each of `transition_to_implementing`, `transition_to_verified`,
`transition_to_approved` (but NOT `transition_to_implemented` — it's not in
the event list from the shaped doc / AC#2), modify the body to dispatch the
hook before returning. Pattern:

```python
def transition_to_implementing(
    project_root: Path,
    issue_number: int,
) -> Path:
    """... (existing docstring unchanged) ..."""
    issue_path = _transition_issue(
        project_root, issue_number, "implementing",
    )
    note, _ = load_issue(issue_path)
    hooks.dispatch(
        "issue-implement-start",
        issue=issue_number,
        status="implementing",
        title=note.title,
        project_dir=project_root,
    )
    return issue_path
```

Repeat the same pattern for `transition_to_verified` (event
`issue-verify-done`, status `"verified"`) and `transition_to_approved`
(event `issue-review-approved`, status `"approved"`).

Do not modify `transition_to_implemented` — the AC#2 list covers only the
four events above, and adding a fifth is scope creep (shaped doc open
question explicitly defers it).

### `src/mantle/core/shaping.py` (modify)

Import `hooks`:

```python
from mantle.core import hooks, project, state, vault
```

In `save_shaped_issue`, locate where the function returns the written path
after a successful save. Immediately before the return, dispatch:

```python
hooks.dispatch(
    "issue-shaped",
    issue=issue_number,
    status=current_status,  # whatever status the issue has now
    title=title,
    project_dir=project_dir,
)
```

The exact variable names will depend on what's already in scope inside
`save_shaped_issue`. The implementer should:

1. Read `core/shaping.py::save_shaped_issue` end-to-end.
2. Identify the `issue` integer, `title` string, and the issue's current
   status (load it via `issues.find_issue_path` + `issues.load_issue` if
   not already in scope — this is the cheapest reliable source). If loading
   the issue adds noise, pass the status the shaping implies (most often
   the issue stays at `"planned"` or `"shaped"` depending on the project's
   status vocabulary; if shaping doesn't transition issue status, use the
   issue's current status).
3. Place the dispatch call at the end of the function, after any state.md
   update or file write succeeds.

### Design decisions

- **Core call-sites, not CLI call-sites**: per system-design.md, CLI is a
  thin forwarder. Putting the dispatch in `core/` means every caller
  (current CLI commands, future API, direct Python callers) gets hooks for
  free. This matches the deep-module pattern from
  `software-design-principles`: dispatch is a hidden detail of the
  transition, not a separate step callers remember to invoke.
- **No try/except at call-site**: `hooks.dispatch()` is guaranteed never to
  raise (story 01's contract). Wrapping it in try/except here would be
  defensive-over-engineering.
- **Title from `load_issue(issue_path)`**: the transition functions don't
  currently take `title` as a parameter. Load the freshly-written note via
  the existing `load_issue` helper (already used inside
  `_transition_issue`). Extra disk hit is negligible; keeps the public
  signature backwards compatible.
- **`transition_to_implemented` NOT wired**: AC#2 lists exactly four
  events. Do not add a fifth.

## Tests

### `tests/core/test_issues.py` (modify)

Add tests in the appropriate transition test class. Each test uses the
existing fixture for a temp project with a seeded issue. Mock
`hooks.dispatch` via `monkeypatch` and assert invocation.

```python
def test_transition_to_implementing_dispatches_hook(tmp_path, monkeypatch):
    # Seed an issue at status=verified so the transition is allowed
    # (reuse whatever helper the existing transition tests use)
    project_dir = _seed_project_with_issue(
        tmp_path, issue=7, title="My Title", status="verified",
    )
    calls = []
    monkeypatch.setattr(
        "mantle.core.issues.hooks.dispatch",
        lambda event, **kw: calls.append((event, kw)),
    )
    issues.transition_to_implementing(project_dir, 7)
    assert calls == [(
        "issue-implement-start",
        {
            "issue": 7,
            "status": "implementing",
            "title": "My Title",
            "project_dir": project_dir,
        },
    )]


def test_transition_to_verified_dispatches_hook(tmp_path, monkeypatch):
    # Parallel to the above — status=implemented → target=verified, event=issue-verify-done
    ...


def test_transition_to_approved_dispatches_hook(tmp_path, monkeypatch):
    # Parallel — status=verified → target=approved, event=issue-review-approved
    ...


def test_failed_transition_does_not_dispatch_hook(tmp_path, monkeypatch):
    # Issue at status=planned → transition_to_verified raises
    # InvalidTransitionError; hook must not fire.
    project_dir = _seed_project_with_issue(
        tmp_path, issue=7, title="X", status="planned",
    )
    calls = []
    monkeypatch.setattr(
        "mantle.core.issues.hooks.dispatch",
        lambda event, **kw: calls.append((event, kw)),
    )
    with pytest.raises(issues.InvalidTransitionError):
        issues.transition_to_verified(project_dir, 7)
    assert calls == []


def test_transition_to_implemented_does_not_dispatch_hook(tmp_path, monkeypatch):
    # Per AC#2, `implemented` is NOT in the event list.
    project_dir = _seed_project_with_issue(
        tmp_path, issue=7, title="X", status="implementing",
    )
    calls = []
    monkeypatch.setattr(
        "mantle.core.issues.hooks.dispatch",
        lambda event, **kw: calls.append((event, kw)),
    )
    issues.transition_to_implemented(project_dir, 7)
    assert calls == []
```

The `_seed_project_with_issue` helper may not exist yet — if so, find the
existing fixture that seeds an issue for transition tests (look for
`test_transition_to_verified` or similar in `tests/core/test_issues.py`)
and extract a small helper, or just inline the setup. Do not over-engineer
the helper.

### `tests/core/test_shaping.py` (modify)

One test, same pattern:

```python
def test_save_shaped_issue_dispatches_hook(tmp_path, monkeypatch):
    # Use the existing fixture that seeds an issue + state.md
    ...
    calls = []
    monkeypatch.setattr(
        "mantle.core.shaping.hooks.dispatch",
        lambda event, **kw: calls.append((event, kw)),
    )
    shaping.save_shaped_issue(..., issue_number=7, ...)
    assert len(calls) == 1
    event, kw = calls[0]
    assert event == "issue-shaped"
    assert kw["issue"] == 7
    assert kw["title"] == "...seeded title..."
    assert kw["project_dir"] == project_dir
    # Don't assert kw["status"] exactly — let it be whatever the issue
    # currently has; just assert it's a non-empty string:
    assert isinstance(kw["status"], str) and kw["status"]
```

**Important**: monkeypatch-attribute paths must target the *imported* name
inside the module being tested (e.g. `mantle.core.issues.hooks.dispatch`,
not `mantle.core.hooks.dispatch`). The shaping tests mock
`mantle.core.shaping.hooks.dispatch`. If the implementer finds the import
is `from mantle.core.hooks import dispatch` instead, adjust the
monkeypatch path accordingly (e.g.
`mantle.core.shaping.dispatch`).

## Acceptance criteria covered by this story

- AC2 (events emitted for: issue-shaped, issue-implement-start,
  issue-verify-done, issue-review-approved) — via the four tests above
- AC4 (hooks directory resolution works for per-project `.mantle/`) —
  exercised by every call-site test that uses a project directory
- AC12 partial (covered by tests for event emission and arg passing) —
  contributes event-emission tests
