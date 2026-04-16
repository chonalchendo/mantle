---
issue: 58
title: Pilot inline_snapshot + dirty-equals + scenario fixture in one vertical slice
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a Mantle contributor, I want inline_snapshot and dirty-equals
available and demonstrated via a scenario fixture, so that I can
migrate future tests away from hand-written expected strings and
attribute-by-attribute assertions.

## Depends On

None — independent (first and only story for issue 58).

## Approach

Single vertical slice per the shaped issue's small-batch approach:
add deps, create `tests/conftest.py` with one canonical named-scenario
fixture, migrate one CLI-output test to `inline_snapshot`, migrate one
round-trip test to `dirty-equals`, document the conventions. All
co-located so the migration proves the conventions end-to-end in one
diff.

## Implementation

### pyproject.toml (modify)

Add `inline-snapshot>=0.19` and `dirty-equals>=0.8` to the `dev`
dependency group. `check` already `include-group = "dev"` so they
flow through to the check group per the acceptance criterion.

After editing, run `uv sync --group check` so `uv.lock` resolves the
new packages.

### tests/conftest.py (new file)

Create a top-level `tests/conftest.py` exporting the
`vault_with_learnings` fixture. Structure:

```python
"""Shared test fixtures for the mantle suite.

Named scenario fixtures describe a specific .mantle/ state so tests
read as specifications of that state rather than walls of setup.
Naming convention: `vault_with_<state>` or `<noun>_after_<event>`.
"""
from __future__ import annotations

from pathlib import Path
import pytest

from mantle.core import issues, vault

_LEARNING_BODY_TEMPLATE = """\
## What went well

- Good thing happened

## Harder than expected

- {harder}

## Wrong assumptions

- {wrong}

## Recommendations

- {rec}
"""


def _write_learning(
    project_dir: Path,
    *,
    issue: int,
    title: str,
    confidence_delta: str,
    harder: str,
    wrong: str,
    rec: str,
) -> None:
    learnings_dir = project_dir / \".mantle\" / \"learnings\"
    learnings_dir.mkdir(parents=True, exist_ok=True)
    slug = title.lower().replace(\" \", \"-\")
    path = learnings_dir / f\"issue-{issue:02d}-{slug}.md\"
    body = _LEARNING_BODY_TEMPLATE.format(harder=harder, wrong=wrong, rec=rec)
    frontmatter = (
        \"---\\n\"
        f\"issue: {issue}\\n\"
        f\"title: {title}\\n\"
        \"author: test@example.com\\n\"
        \"date: '2026-01-01'\\n\"
        f\"confidence_delta: '{confidence_delta}'\\n\"
        \"tags:\\n\"
        \"- type/learning\\n\"
        \"- phase/reviewing\\n\"
        \"---\\n\\n\"
    )
    path.write_text(frontmatter + body, encoding=\"utf-8\")


def _write_issue(
    project_dir: Path,
    *,
    issue: int,
    title: str,
    slice_: tuple[str, ...],
) -> None:
    note = issues.IssueNote(
        title=title,
        status=\"planned\",
        slice=slice_,
        tags=(\"type/issue\", \"status/planned\"),
    )
    slug = title.lower().replace(\" \", \"-\")
    path = (
        project_dir / \".mantle\" / \"issues\" / f\"issue-{issue:02d}-{slug}.md\"
    )
    vault.write_note(path, note, \"## Why\\nx\\n\")


@pytest.fixture
def vault_with_learnings(tmp_path: Path) -> Path:
    \"\"\"Vault state with a core/testing learning (+1) and a cli/worktree
    learning (-1), each with a matching issue file — the canonical
    scenario for pattern/theme rendering tests.
    \"\"\"
    _write_learning(
        tmp_path,
        issue=47,
        title=\"testing-woes\",
        confidence_delta=\"+1\",
        harder=\"pytest fixtures broke\",
        wrong=\"Assumed mock matched prod\",
        rec=\"Use real database\",
    )
    _write_issue(
        tmp_path, issue=47, title=\"testing-woes\", slice_=(\"core\",)
    )
    _write_learning(
        tmp_path,
        issue=48,
        title=\"cli-trouble\",
        confidence_delta=\"-1\",
        harder=\"worktree merge was harder\",
        wrong=\"Assumed branch was clean\",
        rec=\"Use worktree isolation\",
    )
    _write_issue(
        tmp_path, issue=48, title=\"cli-trouble\", slice_=(\"cli\",)
    )
    return tmp_path
```

The exact inputs match the current
`test_render_report_produces_markdown_with_themes_and_trend_table`
so the rendered output is preserved when migrating.

### tests/core/test_patterns.py (modify)

Migrate
`test_render_report_produces_markdown_with_themes_and_trend_table`
only. Delete the inline fixture setup inside that test and replace
with the `vault_with_learnings` fixture parameter. Replace the
~10 `assert X in rendered` lines with a single
`assert rendered == snapshot(\"\"\"...\"\"\")` call.

Run `uv run pytest tests/core/test_patterns.py --inline-snapshot=create`
to auto-fill the snapshot literal, then `--inline-snapshot=review`
to confirm the captured markdown is what's intended. Commit the
resulting literal.

Leave the module-level `_write_learning` / `_write_issue` helpers and
all other tests in the file untouched — the fixture is additive.

### tests/core/test_learning.py (modify)

Migrate `TestSaveLearning.test_round_trip` only. Currently:

```python
assert loaded_note.issue == saved_note.issue
assert loaded_note.title == saved_note.title
assert loaded_note.confidence_delta == (saved_note.confidence_delta)
assert loaded_note.tags == saved_note.tags
```

Replace with:

```python
from dirty_equals import IsPartialDict

assert loaded_note.model_dump() == IsPartialDict({
    \"issue\": 21,
    \"title\": \"Shaping phase implementation\",
    \"confidence_delta\": \"+2\",
    \"tags\": saved_note.tags,
})
```

The `IsPartialDict` tolerates the additional `author`/`date` fields
that Pydantic dumps without requiring us to list them, and reads as a
structural spec rather than four independent field checks.

Import `IsPartialDict` at module top (module-level import per CLAUDE.md
convention).

### CLAUDE.md (modify)

Append to the existing `## Test Conventions` section (keep existing
bullets; add new sub-bullets at the bottom):

```markdown
- Use `inline_snapshot` (`from inline_snapshot import snapshot`) for
  tests asserting exact-string CLI output, rendered markdown, or
  generated artefacts. `assert rendered == snapshot()` starts empty and
  is auto-filled by `uv run pytest --inline-snapshot=create`; review
  the diff before committing. Never hand-edit a snapshot literal.
- Use `dirty-equals` (`IsPartialDict`, `IsList(..., check_order=False)`,
  `IsDatetime`, `IsNow`, `IsStr(regex=...)`) for partial or unordered
  comparisons — replaces hand-written attribute-by-attribute asserts
  and sort-then-compare helpers. Pair with `inline_snapshot` for
  captures that need to tolerate unstable fields.
- Scenario fixtures in `tests/conftest.py` follow the naming
  convention `vault_with_<state>` or `<noun>_after_<event>`; the
  docstring describes the scenario. One fixture = one named scenario.
- Don't mix the two tools in a single assertion without intent:
  `inline_snapshot` captures values, `dirty-equals` captures shape.
```

### system-design.md (modify)

Locate the existing \"Test Tooling\" / \"Testing\" section. Append
one line:

```markdown
- `inline_snapshot` and `dirty-equals` are available for exact-output
  capture and structural comparison respectively (see CLAUDE.md Test
  Conventions).
```

If no Test Tooling section exists, add it under the testing-related
heading; keep the addition to a single bullet.

#### Design decisions

- **Deps in `dev` not `check` directly**: `check` includes `dev` via
  `include-group`, so adding to `dev` satisfies the AC and keeps
  test-only deps co-located with other test deps (pytest, pytest-cov).
- **One fixture, not three**: the issue explicitly calls for \"at least
  one\" fixture; overshooting at pilot stage defeats the \"prove
  conventions before sweeping\" intent.
- **Migrate `test_round_trip` not `test_correct_frontmatter` for
  dirty-equals**: `test_round_trip` compares two objects
  (loaded vs saved), which is where partial-dict matching shows value;
  `test_correct_frontmatter` uses literal expected values and would be
  a forced demo.
- **Don't rewrite the `_write_learning`/`_write_issue` helpers inside
  `test_patterns.py`**: only the migrated test consumes the fixture;
  other tests in that file keep their local helpers. A follow-up issue
  can extract them if the convention proves its worth.

## Tests

### tests/core/test_patterns.py (modify existing test)

- **test_render_report_produces_markdown_with_themes_and_trend_table**:
  now consumes `vault_with_learnings` and asserts full rendered
  markdown matches an `inline_snapshot` literal (no more `in`
  assertions for theme names, table rows, slice ordering — the whole
  captured literal is the spec).

### tests/core/test_learning.py (modify existing test)

- **TestSaveLearning.test_round_trip**: asserts
  `loaded_note.model_dump() == IsPartialDict({...stable fields...})`
  instead of four attribute-by-attribute asserts. Verifies dirty-equals
  tolerates the unstable author/date fields.

### Verification

- `uv run pytest tests/core/test_patterns.py tests/core/test_learning.py -v`
  — the two migrated tests pass.
- `uv run pytest` — full suite still 1145 passing (no regression).
- `just check` — all lint/type/tests green.