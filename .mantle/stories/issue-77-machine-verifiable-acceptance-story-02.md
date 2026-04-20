---
issue: 77
title: CLI surface, verify/review prompt wiring, and backfill live backlog
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a reviewer using `/mantle:review`, I want a `flip-ac` CLI and updated verify/review prompts so that the pass/fail machinery in story 1 is actually reachable from the workflow — and I want the live backlog backfilled so structured ACs apply to existing issues, not just new ones.

## Depends On

Story 1 — this story wires the CLI and prompt layers into the core acceptance module and `flip_acceptance_criterion` / `migrate_all_acs` public API added there.

## Approach

Thin cyclopts wrappers in `cli/issues.py` expose `flip-ac`, `list-acs`, and `migrate-acs` to the Claude prompts and terminal users. Update `verify.md` and `review.md` to fetch ACs via `mantle list-acs --json` and flip via `mantle flip-ac` instead of grepping the body. Run `mantle migrate-acs` once at the tail of the story so the existing backlog moves to structured form in the same commit. Follows the thin-CLI pattern of `cli/issues.py::run_save_issue` and the prompt-invokes-CLI pattern used by the existing `save-review-result` flow.

## Implementation

### src/mantle/cli/issues.py (modify)

Add three runner functions and matching cyclopts registrations:

```python
from __future__ import annotations

import json
from pathlib import Path

from rich.console import Console
from rich.table import Table

from mantle.cli import errors
from mantle.core import acceptance, issues

console = Console()


def run_flip_ac(
    *,
    issue: int,
    ac_id: str,
    passes: bool = True,
    waive: bool = False,
    reason: str | None = None,
    project_dir: Path | None = None,
) -> None:
    \"\"\"Flip one acceptance criterion to pass/fail or waive it.

    --pass and --fail are mutually exclusive with --waive. When
    --waive is set, passes stays False but the gate treats the
    criterion as resolved.
    \"\"\"
    if project_dir is None:
        project_dir = Path.cwd()
    if waive and reason is None:
        errors.exit_with_error(\"--waive requires --reason\")

    try:
        updated = issues.flip_acceptance_criterion(
            project_dir,
            issue,
            ac_id,
            passes=passes and not waive,
            waived=waive,
            waiver_reason=reason,
        )
    except acceptance.CriterionNotFoundError as exc:
        errors.exit_with_error(str(exc))
    except FileNotFoundError as exc:
        errors.exit_with_error(str(exc))

    match = next(
        (c for c in updated.acceptance_criteria if c.id == ac_id),
        None,
    )
    state_label = (
        \"waived\"
        if match and match.waived
        else \"pass\"
        if match and match.passes
        else \"fail\"
    )
    console.print(
        f\"[green]issue-{issue:02d}[/green] {ac_id} → {state_label}\"
    )


def run_list_acs(
    *,
    issue: int,
    json_output: bool = False,
    project_dir: Path | None = None,
) -> None:
    \"\"\"Print an issue's acceptance criteria as a table or JSON.

    Claude prompts invoke this with --json to read structured
    output; humans see a table.
    \"\"\"
    if project_dir is None:
        project_dir = Path.cwd()
    issue_path = issues.find_issue_path(project_dir, issue)
    if issue_path is None:
        errors.exit_with_error(f\"Issue {issue} not found\")
    note, _ = issues.load_issue(issue_path)

    if json_output:
        payload = [
            c.model_dump(mode=\"json\") for c in note.acceptance_criteria
        ]
        console.print_json(data=payload)
        return

    table = Table(title=f\"Issue {issue} acceptance criteria\")
    table.add_column(\"id\")
    table.add_column(\"state\")
    table.add_column(\"text\")
    for c in note.acceptance_criteria:
        state = (
            \"waived\" if c.waived else (\"pass\" if c.passes else \"fail\")
        )
        table.add_row(c.id, state, c.text)
    console.print(table)


def run_migrate_acs(
    *,
    dry_run: bool = False,
    project_dir: Path | None = None,
) -> None:
    \"\"\"Backfill markdown-checkbox ACs into structured frontmatter.

    Scans .mantle/issues/ and .mantle/archive/issues/. Issues that
    already have structured ACs are skipped.
    \"\"\"
    if project_dir is None:
        project_dir = Path.cwd()

    if dry_run:
        # reuse issues.load_issue + acceptance.parse_ac_section
        # purely for reporting — do NOT write.
        paths = (
            issues.list_issues(project_dir)
            + issues.list_archived_issues(project_dir)
        )
        console.print(\"[bold]dry-run — no writes[/bold]\")
        for path in paths:
            note, body = issues.load_issue(path)
            if note.acceptance_criteria:
                continue
            parsed = acceptance.parse_ac_section(body)
            if parsed:
                console.print(
                    f\"would migrate {path.name}: {len(parsed)} criteria\"
                )
        return

    results = issues.migrate_all_acs(project_dir)
    if not results:
        console.print(\"[yellow]No issues needed migration.[/yellow]\")
        return
    for number, count in results:
        console.print(f\"migrated issue-{number:02d}: {count} criteria\")
    console.print(
        f\"[green]Migrated {len(results)} issue(s).[/green]\"
    )
```

### src/mantle/cli/main.py (modify)

Register three commands under the existing `app` (or the appropriate sub-app, matching where `run_save_issue` is registered). Use the idiomatic cyclopts pattern already used by `save-issue`, `transition-issue-verified`, etc.:

```python
from mantle.cli.issues import run_flip_ac, run_list_acs, run_migrate_acs

@app.command(name=\"flip-ac\")
def flip_ac_cmd(
    *,
    issue: int,
    ac_id: Annotated[str, Parameter(name=\"--ac-id\")],
    passes: Annotated[bool, Parameter(name=\"--pass/--fail\")] = True,
    waive: bool = False,
    reason: str | None = None,
) -> None:
    \"\"\"Flip one acceptance criterion's pass/fail state.\"\"\"
    run_flip_ac(
        issue=issue,
        ac_id=ac_id,
        passes=passes,
        waive=waive,
        reason=reason,
    )


@app.command(name=\"list-acs\")
def list_acs_cmd(
    *,
    issue: int,
    json_output: Annotated[bool, Parameter(name=\"--json\")] = False,
) -> None:
    \"\"\"Print an issue's structured acceptance criteria.\"\"\"
    run_list_acs(issue=issue, json_output=json_output)


@app.command(name=\"migrate-acs\")
def migrate_acs_cmd(*, dry_run: bool = False) -> None:
    \"\"\"Backfill markdown AC checkboxes into structured frontmatter.\"\"\"
    run_migrate_acs(dry_run=dry_run)
```

Before wiring, **grep `cli/main.py` to confirm the exact decorator / sub-app pattern already in use** — match it rather than inventing a new one.

### claude/commands/mantle/verify.md (modify)

1. **Step 5 — Load acceptance criteria** — replace the body-grep instructions with:
   ```
   Run `mantle list-acs --issue {NN} --json` to load the structured
   acceptance criteria. Display them with their ids and current
   pass/fail state.
   ```
2. **Step 6 — Execute verification** — add a trailing paragraph:
   ```
   After gathering evidence for each criterion, record the result via
   the CLI — never by editing the issue file directly:

       mantle flip-ac --issue {NN} --ac-id <ac-id> --pass
       # or
       mantle flip-ac --issue {NN} --ac-id <ac-id> --fail

   Every `--pass` must cite the evidence. If you cannot produce
   evidence, use `--fail`.
   ```
3. **Step 7 — Report results** — add: after the per-criterion table, run `mantle list-acs --issue {NN}` one more time and include any criteria still at `passes: false` at the end of the report as the definitive failing list.

### claude/commands/mantle/review.md (modify)

1. **Step 3 — Load verification results** — replace body-grep with:
   ```
   Run `mantle list-acs --issue {NN} --json` to load the structured
   AC list. Any criterion with `passes: false` and `waived: false`
   blocks approval.
   ```
2. **Step 6 — Handle outcome** — in the approval branch, note that `mantle transition-issue-approved` will now raise `UnresolvedAcceptanceCriteriaError` if any AC is unresolved. On that error, report the failing ids and stop — do not archive.

### Backfill the live backlog

At the end of this story (after tests pass), run:

    uv run mantle migrate-acs

and commit the resulting frontmatter/body changes to the same commit as the rest of this story. This delivers AC 5 on the existing backlog.

#### Design decisions

- **`--pass/--fail` as a `bool`**, matching the cyclopts idiom demonstrated in the skill. No separate `--mark-failed` flag.
- **`--waive` requires `--reason`** — waivers without rationale are exactly the gaming vector the issue is designed to prevent.
- **JSON output uses `console.print_json`** so rich auto-handles quoting; prompts parse with `json.loads` on the captured stdout.
- **Migration runs against both live and archive** because an approved archived issue may still be referenced by a retrospective — structured ACs help future `/mantle:patterns` queries.

## Tests

### tests/cli/test_issues.py (new file — match existing cli test conventions)

Use the cyclopts testing idiom from the skill: construct the `app`, call `app(\"flip-ac --issue 1 --ac-id ac-01\", result_action=\"return_value\")`, assert on side effects in `tmp_path`.

- **test_flip_ac_marks_pass**: save a tmp issue with one pending AC, run `flip-ac ... --pass`, reload — `passes=True`, body shows `[x]`.
- **test_flip_ac_marks_fail**: same but `--fail` — `passes=False`.
- **test_flip_ac_waive_requires_reason**: running `flip-ac --waive` without `--reason` exits with code 1 and stderr explains the rule.
- **test_flip_ac_unknown_id_exits_1**: unknown `ac-id` exits with code 1 and the error names the missing id.
- **test_list_acs_json_matches_frontmatter**: save tmp issue with two ACs, run `list-acs --json`, parse stdout — matches `[{\"id\": ..., \"passes\": ...}, ...]` via `dirty_equals.IsList`.
- **test_list_acs_table_contains_ids**: non-JSON output includes each ac-id string.
- **test_migrate_acs_reports_zero_when_nothing_to_do**: empty tmp vault → stdout mentions \"No issues needed migration\".
- **test_migrate_acs_migrates_legacy_checkboxes**: tmp issue with `- [ ] First` and `- [x] Second` under `## Acceptance criteria` — after `migrate-acs`, frontmatter has two ACs with `passes=[False, True]` and stdout lists one migrated issue.
- **test_migrate_acs_dry_run_writes_nothing**: same setup with `--dry-run` — file is unchanged, stdout still lists the would-be migration.

### claude/commands/mantle/verify.md + review.md

No unit tests — these are prompt edits. Instead, verify at the end of the story that:

- `grep 'list-acs' claude/commands/mantle/verify.md` and `review.md` return hits.
- `grep 'flip-ac' claude/commands/mantle/verify.md` returns at least one hit.

These greps are part of the story's hand-off evidence for the implementer.

### Final hand-off checklist for the implementer

1. `uv run pytest tests/` — all green.
2. `just check` — all green.
3. `uv run mantle migrate-acs` against this project — commits the backfilled issue files.
4. `uv run mantle list-acs --issue 77 --json | jq '.[] | .id'` returns seven ids (ac-01..ac-07) — proves end-to-end round-trip on the live issue.