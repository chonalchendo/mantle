---
issue: 77
title: Core acceptance-criteria module, IssueNote integration, and approval gate
status: in-progress
failure_log: null
tags:
- type/story
- status/in-progress
---

## User Story

As an agent running `/mantle:verify`, I want acceptance criteria stored as a structured Pydantic list in issue frontmatter so that `passes` is an unambiguous field I flip after evidence-based verification, not a checkbox I infer from prose.

## Depends On

None — foundation story.

## Approach

Introduce a new `core/acceptance.py` module holding the pure logic: a frozen Pydantic `AcceptanceCriterion` model, rendering the canonical markdown view, parsing existing body checklists for migration, and mutating a criterion tuple by id. Extend `core/issues.py::IssueNote` with the new field, regenerate the body's `## Acceptance criteria` section on every save, and gate `transition_to_approved` behind `all_acs_pass_or_waived`. All of this is testable without touching the CLI or Claude prompts — story 2 builds on this foundation.

## Implementation

### src/mantle/core/acceptance.py (new file)

Pure module, no side effects, no CLI or vault imports.

```python
from __future__ import annotations

import re
from typing import TYPE_CHECKING

import pydantic


class AcceptanceCriterion(pydantic.BaseModel, frozen=True):
    \"\"\"Single acceptance criterion with pass/fail state.\"\"\"

    id: str  # e.g. 'ac-01'
    text: str
    passes: bool = False
    waived: bool = False
    waiver_reason: str | None = None


class CriterionNotFoundError(Exception):
    def __init__(self, ac_id: str) -> None:
        self.ac_id = ac_id
        super().__init__(f\"Acceptance criterion '{ac_id}' not found\")


class DuplicateCriterionIdError(Exception):
    def __init__(self, ac_id: str) -> None:
        self.ac_id = ac_id
        super().__init__(f\"Duplicate acceptance criterion id '{ac_id}'\")


# ── Pure helpers ─────────────────────────────────────────────────

def render_ac_section(
    criteria: tuple[AcceptanceCriterion, ...],
) -> str:
    \"\"\"Render the canonical '## Acceptance criteria' markdown block.

    Example output:

        ## Acceptance criteria

        - [x] ac-01: Frontmatter has an acceptance_criteria list ...
        - [ ] ac-02: Markdown checkboxes are generated on save ...
    \"\"\"
    if not criteria:
        return \"## Acceptance criteria\\n\\n_None defined._\\n\"
    lines = [\"## Acceptance criteria\", \"\"]
    for c in criteria:
        box = \"[x]\" if c.passes or c.waived else \"[ ]\"
        suffix = \" (waived)\" if c.waived and not c.passes else \"\"
        lines.append(f\"- {box} {c.id}: {c.text}{suffix}\")
    lines.append(\"\")
    return \"\\n\".join(lines)


_AC_SECTION_RE = re.compile(
    r\"(?ms)^##\\s+Acceptance\\s+criteria\\b.*?(?=^##\\s|\\Z)\"
)


def replace_ac_section(body: str, rendered: str) -> str:
    \"\"\"Swap the '## Acceptance criteria' section, appending if absent.

    - If the body already has a section matching \`^## Acceptance criteria\`
      (case-insensitive on the heading word), swap its contents for
      \`rendered\`.
    - If absent, append \`rendered\` to the body (separated by a blank
      line).
    \"\"\"
    if _AC_SECTION_RE.search(body):
        return _AC_SECTION_RE.sub(rendered.rstrip() + \"\\n\\n\", body, count=1)
    separator = \"\\n\\n\" if body and not body.endswith(\"\\n\\n\") else \"\"
    return body + separator + rendered


_CHECKBOX_RE = re.compile(
    r\"^\\s*-\\s*\\[(?P<box>[ xX])\\]\\s*(?P<text>.+?)\\s*$\"
)


def parse_ac_section(
    body: str,
) -> tuple[AcceptanceCriterion, ...]:
    \"\"\"Extract legacy markdown checkboxes from body for migration.

    Scans lines under \`## Acceptance criteria\` (until the next
    top-level heading) and returns structured criteria with
    auto-assigned ids \`ac-01..N\`. Passes = checkbox is checked.
    Returns \`()\` when the section is missing or empty.
    \"\"\"
    match = _AC_SECTION_RE.search(body)
    if not match:
        return ()
    section = match.group(0)
    lines = section.splitlines()[1:]  # skip the heading
    items: list[AcceptanceCriterion] = []
    for line in lines:
        m = _CHECKBOX_RE.match(line)
        if not m:
            continue
        raw_text = m.group(\"text\").strip()
        # Strip any pre-existing 'ac-NN: ' prefix so re-parse is a no-op.
        cleaned = re.sub(r\"^ac-\\d{2}:\\s*\", \"\", raw_text)
        passes = m.group(\"box\").lower() == \"x\"
        items.append(
            AcceptanceCriterion(
                id=f\"ac-{len(items) + 1:02d}\",
                text=cleaned,
                passes=passes,
            )
        )
    return tuple(items)


def flip_criterion(
    criteria: tuple[AcceptanceCriterion, ...],
    ac_id: str,
    *,
    passes: bool,
    waived: bool = False,
    waiver_reason: str | None = None,
) -> tuple[AcceptanceCriterion, ...]:
    \"\"\"Return a new tuple with the matching criterion mutated.

    Raises CriterionNotFoundError if ac_id is absent.
    \"\"\"
    found = False
    out: list[AcceptanceCriterion] = []
    for c in criteria:
        if c.id == ac_id:
            out.append(
                c.model_copy(
                    update={
                        \"passes\": passes,
                        \"waived\": waived,
                        \"waiver_reason\": waiver_reason,
                    }
                )
            )
            found = True
        else:
            out.append(c)
    if not found:
        raise CriterionNotFoundError(ac_id)
    return tuple(out)


def all_pass_or_waived(
    criteria: tuple[AcceptanceCriterion, ...],
) -> bool:
    \"\"\"True when every criterion either passes or is waived.

    Returns True on an empty tuple — issues without ACs cannot block
    approval.
    \"\"\"
    return all(c.passes or c.waived for c in criteria)


def assert_unique_ids(
    criteria: tuple[AcceptanceCriterion, ...],
) -> None:
    \"\"\"Raise DuplicateCriterionIdError if any id repeats.\"\"\"
    seen: set[str] = set()
    for c in criteria:
        if c.id in seen:
            raise DuplicateCriterionIdError(c.id)
        seen.add(c.id)
```

### src/mantle/core/issues.py (modify)

1. Import `acceptance` at module top.
2. Extend `IssueNote`:
   ```python
   from mantle.core.acceptance import AcceptanceCriterion

   class IssueNote(pydantic.BaseModel, frozen=True):
       ...
       acceptance_criteria: tuple[AcceptanceCriterion, ...] = ()
   ```
3. Modify `save_issue` just before `vault.write_note(issue_path, note, content)`:
   ```python
   if note.acceptance_criteria:
       acceptance.assert_unique_ids(note.acceptance_criteria)
       content = acceptance.replace_ac_section(
           content,
           acceptance.render_ac_section(note.acceptance_criteria),
       )
   vault.write_note(issue_path, note, content)
   ```
   Do NOT regenerate when `acceptance_criteria == ()` — preserves behaviour for callers that haven't migrated yet (story 2 backfills).
4. Add a new public function:
   ```python
   class UnresolvedAcceptanceCriteriaError(Exception):
       def __init__(self, issue_number: int, failing: tuple[str, ...]) -> None:
           self.issue_number = issue_number
           self.failing = failing
           super().__init__(
               f\"Issue {issue_number} has unresolved ACs: {', '.join(failing)}\"
           )

   def flip_acceptance_criterion(
       project_dir: Path,
       issue_number: int,
       ac_id: str,
       *,
       passes: bool,
       waived: bool = False,
       waiver_reason: str | None = None,
   ) -> IssueNote:
       issue_path = find_issue_path(project_dir, issue_number)
       if issue_path is None:
           raise FileNotFoundError(f\"Issue {issue_number} not found\")
       note, body = load_issue(issue_path)
       new_criteria = acceptance.flip_criterion(
           note.acceptance_criteria,
           ac_id,
           passes=passes,
           waived=waived,
           waiver_reason=waiver_reason,
       )
       updated = note.model_copy(update={\"acceptance_criteria\": new_criteria})
       body = acceptance.replace_ac_section(
           body,
           acceptance.render_ac_section(new_criteria),
       )
       vault.write_note(issue_path, updated, body)
       return updated
   ```
5. Add migration:
   ```python
   def migrate_all_acs(project_dir: Path) -> list[tuple[int, int]]:
       \"\"\"Parse markdown checkboxes into structured ACs for every issue.

       Returns a list of (issue_number, criteria_count) tuples. Skips
       issues that already have acceptance_criteria set.
       \"\"\"
       results: list[tuple[int, int]] = []
       paths = list_issues(project_dir) + list_archived_issues(project_dir)
       for path in paths:
           note, body = load_issue(path)
           if note.acceptance_criteria:
               continue  # already migrated
           parsed = acceptance.parse_ac_section(body)
           if not parsed:
               continue
           updated = note.model_copy(update={\"acceptance_criteria\": parsed})
           new_body = acceptance.replace_ac_section(
               body,
               acceptance.render_ac_section(parsed),
           )
           vault.write_note(path, updated, new_body)
           m = re.match(r\"issue-(\\d+)-\", path.name)
           number = int(m.group(1)) if m else -1
           results.append((number, len(parsed)))
       return results
   ```
6. Modify `transition_to_approved` to gate on ACs before calling `_transition_issue`:
   ```python
   def transition_to_approved(project_root: Path, issue_number: int) -> Path:
       issue_path = find_issue_path(project_root, issue_number)
       if issue_path is None:
           raise FileNotFoundError(f\"Issue {issue_number} not found\")
       note, _ = load_issue(issue_path)
       if note.acceptance_criteria and not acceptance.all_pass_or_waived(
           note.acceptance_criteria
       ):
           failing = tuple(
               c.id
               for c in note.acceptance_criteria
               if not (c.passes or c.waived)
           )
           raise UnresolvedAcceptanceCriteriaError(issue_number, failing)
       # existing transition logic ...
   ```

#### Design decisions

- **`acceptance_criteria: tuple = ()` as a default** so existing issues keep working without frontmatter changes until story 2 migrates them.
- **Body regen only when the list is non-empty**: avoids touching any unmigrated issue.
- **`all_pass_or_waived` returns True for empty tuple**: consistent with existing issues — the gate only applies once the list exists.
- **Gate lives on `transition_to_approved` only**, not `transition_to_verified` — verify flips ACs one at a time and should not itself be blocked.
- **Exception types in `core/issues.py` not `core/acceptance.py`** for issue-number-bearing errors; `core/acceptance.py` keeps tuple-level errors only.

## Tests

### tests/core/test_acceptance.py (new file)

- **test_acceptance_criterion_is_frozen**: mutating a field raises `pydantic.ValidationError`.
- **test_render_ac_section_snapshot**: `render_ac_section(...)` for a canonical 3-item list — `inline_snapshot` for exact markdown.
- **test_render_empty_shows_placeholder**: `render_ac_section(())` returns the `_None defined._` placeholder.
- **test_replace_ac_section_swaps_existing**: body with an old AC section gets the new section in the same slot.
- **test_replace_ac_section_appends_when_absent**: body without the section gets the rendered block appended.
- **test_parse_ac_section_assigns_ids_in_order**: legacy checkboxes produce `ac-01`, `ac-02`, ...
- **test_parse_ac_section_roundtrip_preserves_ids**: `parse_ac_section(render_ac_section(criteria))` returns the same ids and text.
- **test_parse_ac_section_passes_from_checkbox_state**: `- [x]` → `passes=True`, `- [ ]` → `passes=False`.
- **test_parse_ac_section_returns_empty_when_section_missing**: body with no AC heading returns `()`.
- **test_flip_criterion_mutates_matching_id**: returns a new tuple with one criterion updated.
- **test_flip_criterion_raises_on_missing_id**: `CriterionNotFoundError`.
- **test_all_pass_or_waived_true_on_empty**: empty tuple returns `True`.
- **test_all_pass_or_waived_false_when_any_pending**: mixed tuple with one pending returns `False`.
- **test_all_pass_or_waived_true_when_waived_counts**: a waived criterion with `passes=False` satisfies the gate.
- **test_assert_unique_ids_raises_on_duplicate**: `DuplicateCriterionIdError`.

### tests/core/test_issues.py (modify)

- **test_save_issue_regenerates_ac_section_in_body**: save with `acceptance_criteria=(ac-01, ac-02)` and body containing a stale `## Acceptance criteria` section — reload and assert the body reflects the structured list (`inline_snapshot` for the AC section only).
- **test_save_issue_preserves_body_when_criteria_empty**: save with `acceptance_criteria=()` — body is untouched.
- **test_flip_acceptance_criterion_updates_passes_and_body**: save an issue, flip `ac-01`, reload — frontmatter has `passes=True` and body shows `[x]`.
- **test_flip_acceptance_criterion_raises_on_unknown_ac**: `CriterionNotFoundError`.
- **test_transition_to_approved_blocks_when_ac_pending**: save issue with `status='verified'` and one pending AC — `UnresolvedAcceptanceCriteriaError`, `failing=('ac-01',)`.
- **test_transition_to_approved_allows_when_all_pass**: all `passes=True` — transitions cleanly.
- **test_transition_to_approved_allows_when_waived**: one waived, rest pass — transitions cleanly.
- **test_transition_to_approved_still_works_with_empty_criteria**: existing issues without ACs still approve (backwards compat).
- **test_migrate_all_acs_converts_markdown_checkboxes**: build a tmp `.mantle/issues/issue-01-foo.md` with `- [ ] First` / `- [x] Second` — `migrate_all_acs` writes structured ACs and regenerates body; reload and assert.
- **test_migrate_all_acs_skips_already_migrated**: issue with non-empty `acceptance_criteria` is not touched.
- **test_migrate_all_acs_covers_archive**: archived issue gets migrated too.

Use `tmp_path` fixtures and `dirty_equals.IsPartialDict` where frontmatter comparisons need to tolerate other fields.