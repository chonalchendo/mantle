---
issue: 57
title: save-learning silently writes after issue archived
appetite: small
chosen_approach: strict
status: shaped
tags:
  - type/shaped
---

## Context

`mantle save-learning --issue NN` silently writes to
`.mantle/learnings/` even when the target issue has been moved to
`.mantle/archive/issues/`. Same family as the side-effect-ordering bugs
fixed in issues 46, 47, and 49. The regression test
`tests/test_staleness_regressions.py::TestArchiveSideEffects::test_save_learning_after_archive_fails_clearly`
is currently marked `xfail(strict=False)` and will flip to a real pass
once fixed.

## Approaches Considered

### 1. Strict — fail loudly when issue is not in `.mantle/issues/` (chosen)

- `save_learning` gains a precondition: call
  `issues.find_issue_path(project_dir, issue)`; if `None`, raise a new
  `IssueNotFoundError(issue)`.
- CLI shim catches it, prints an actionable message to stderr, exits 1.
- Matches the existing `find_issue_path` contract and the precedent
  from earlier staleness fixes (same shape as `update_story_status`
  path guard).
- **Appetite: small.** ~15 lines of production code, one new
  exception, one CLI catch branch, no schema changes.

### 2. Permissive — look up archived path and annotate

- Adds `archived_issue_path: str | None` to `LearningNote`.
- Loader walks both `.mantle/issues/` and `.mantle/archive/issues/`.
- Any learning consumer (`/mantle:patterns`, retro flow) must handle
  the annotated case.
- **Rejected:** frontmatter schema churn, more test surface, and
  the existing retro flow is gated on issue state before archival
  anyway — post-archive retros are the pathological case we want
  to reject, not normalise.

### 3. Do nothing (baseline)

- Current behaviour: silent success, orphaned learning, xfail test
  remains xfail forever.
- **Rejected:** the issue exists precisely because this is unsafe.

## Chosen Approach — Strict

### Code design

**`src/mantle/core/learning.py`**

Add a new exception alongside `LearningExistsError`:

```python
class IssueNotFoundError(Exception):
    """Raised when save-learning targets an unknown / archived issue."""

    def __init__(self, issue: int) -> None:
        self.issue = issue
        super().__init__(
            f"Issue {issue} not found in .mantle/issues/ "
            f"(may have been archived)"
        )
```

In `save_learning`, add the precondition *before* any mutation:

```python
if issues.find_issue_path(project_dir, issue) is None:
    raise IssueNotFoundError(issue)
```

Placed immediately after `_validate_confidence_delta` so we fail
before computing paths, reading identity, or touching `state.md`.

**`src/mantle/cli/learning.py`**

Extend the existing try/except to catch the new error and emit an
actionable message, following the same pattern as the other
guards in the CLI layer:

```python
except learning.IssueNotFoundError as exc:
    console.print(
        f"[red]Error:[/red] {exc}\n"
        f"  If the issue is archived, save the learning before"
        f" running /mantle:archive, or edit the archived issue"
        f" file directly."
    )
    raise SystemExit(1) from None
```

### Tests

- Flip the `xfail` marker off
  `test_save_learning_after_archive_fails_clearly`; it asserts
  non-zero exit + "not found" or "archive" in output, both of which
  the new error message satisfies.
- Add a direct core-layer test in
  `tests/core/test_learning.py` (if it exists; otherwise alongside
  existing learning tests) that calls `save_learning` for an
  unknown issue number and asserts `IssueNotFoundError` is raised
  *and* no file is written under `.mantle/learnings/`.

### Acceptance criteria mapping

| AC | Satisfied by |
|----|--------------|
| save-learning exits non-zero with clear error when issue not found | CLI catch branch + exit 1 |
| Staleness regression test flips from xfail to pass | Remove `@pytest.mark.xfail` decorator |
| Existing learning tests still pass | Precondition fires only on missing issue; happy path unchanged |
| `just check` passes | Ruff/type-clean additions |

## Out of Scope

- Backfilling existing orphaned learnings.
- Permissive annotation of archived-issue learnings (option 2).
- Auditing the full command surface for similar staleness bugs
  (tracked separately in inbox / issues 46-49-56 lineage).

## Skills read

- `software-design-principles` → `.claude/skills/software-design-principles/references/core.md`
- `cli-design-best-practices` → `.claude/skills/cli-design-best-practices/references/core.md`
- `cyclopts` → `.claude/skills/cyclopts/references/core.md`
- `design-review` → `.claude/skills/design-review/references/core.md`
