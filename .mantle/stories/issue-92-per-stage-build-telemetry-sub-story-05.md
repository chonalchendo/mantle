---
issue: 92
title: 'Template instrumentation: mantle stage-begin in every LLM-invoking /mantle:*
  template + parity snapshot refresh'
status: planned
failure_log: null
tags:
- type/story
- status/planned
---

## User Story

As a developer running any LLM-invoking `/mantle:*` command (inside or outside `/mantle:build`), I want the command template to emit a `mantle stage-begin <name>` at entry, so that the session's token usage is attributable to that stage in downstream reports.

## Depends On

Story 2 — every template invocation requires the `mantle stage-begin` CLI command to exist. Without Story 2, the edits break every template on first run.

## Approach

Mechanical edit across ~22 `.md` templates in `claude/commands/mantle/`: insert `mantle stage-begin <stage-name>` as the **first shell call** in each template body — immediately before any existing `MANTLE_DIR=$(mantle where)` line. Stage names follow the rule in the shaped doc: match `cost-policy.md` keys (`shape`, `plan_stories`, `implement`, `simplify`, `verify`, `review`, `retrospective`) where applicable; match the command slug otherwise. `build.md` gets two additional inline emissions at Step 4 (`shape`) and Step 5 (`plan_stories`). Refresh the 3 integrated parity-harness snapshots (`build`, `implement`, `plan-stories`) via `--inline-snapshot=create`; review the diffs; commit.

## Implementation

### claude/commands/mantle/*.md (modify 22 files)

**Instrumented templates** — add `mantle stage-begin <stage-name>` as the first shell-mode command call (before `MANTLE_DIR=$(mantle where)` or any other `mantle`/`bash` invocation). Use plain shell inline, no code-fence if the template already runs commands inline; match the existing template's convention.

| Template                | Stage name        | Source of name            |
|-------------------------|-------------------|---------------------------|
| `build.md`              | `build`           | command slug              |
| `shape-issue.md`        | `shape`           | cost-policy key           |
| `plan-stories.md`       | `plan_stories`    | cost-policy key           |
| `plan-issues.md`        | `plan-issues`     | command slug              |
| `implement.md`          | `implement`       | cost-policy key           |
| `simplify.md`           | `simplify`        | cost-policy key           |
| `verify.md`             | `verify`          | cost-policy key           |
| `review.md`             | `review`          | cost-policy key           |
| `retrospective.md`      | `retrospective`   | cost-policy key           |
| `fix.md`                | `fix`             | command slug              |
| `challenge.md`          | `challenge`       | command slug              |
| `design-product.md`     | `design-product`  | command slug              |
| `design-system.md`      | `design-system`   | command slug              |
| `revise-product.md`     | `revise-product`  | command slug              |
| `revise-system.md`      | `revise-system`   | command slug              |
| `brainstorm.md`         | `brainstorm`      | command slug              |
| `research.md`           | `research`        | command slug              |
| `scout.md`              | `scout`           | command slug              |
| `adopt.md`              | `adopt`           | command slug              |
| `refactor.md`           | `refactor`        | command slug              |
| `idea.md`               | `idea`            | command slug              |
| `patterns.md`           | `patterns`        | command slug              |
| `distill.md`            | `distill`         | command slug              |

**Skip list** (wiring / short non-reasoning templates — no stage marker):

- `help.md`, `resume.md.j2`, `status.md.j2`
- `add-issue.md`, `add-skill.md`, `bug.md`, `inbox.md`, `query.md`

If on closer inspection any template in the skip list has LLM reasoning, the implementer adds it to the instrumented set and flags in the commit message. The parity harness + AC-06 enforces that every non-skipped LLM-invoking template emits the line.

**`build.md` additional edits** — `build.md` runs shape and plan-stories inline (Steps 4 and 5) rather than via nested slash-command invocations, so it emits its own inline stage marks:

- At the start of Step 4 (before any \"If not shaped\" reasoning): `mantle stage-begin shape`
- At the start of Step 5 (before \"If not planned\" reasoning): `mantle stage-begin plan_stories`

Add each as a plain-shell line in prose: `Before proceeding, run: `mantle stage-begin shape`.` Exact wording follows the template's existing prose style.

**`allowed-tools` frontmatter update** — every edited template's `allowed-tools` already permits `Bash(mantle *)`; verify via grep that this is true and no template needs narrowing adjustment. If any template has a narrower `Bash(mantle ...)` allow-list, widen it to include `Bash(mantle stage-begin*)`.

### tests/parity/test_build_parity.py (modify)
### tests/parity/test_implement_parity.py (modify)
### tests/parity/test_plan_stories_parity.py (modify)

Regenerate all three `snapshot(\"\"\"...\"\"\")` baselines:

```bash
uv run pytest --inline-snapshot=create tests/parity/test_build_parity.py tests/parity/test_implement_parity.py tests/parity/test_plan_stories_parity.py
```

Review the diff manually before committing — confirm the only change is insertion of `mantle stage-begin <name>` + (for build) two inline Step 4/5 lines. Reject any normalisation-field drift (timestamps, absolute paths, session IDs).

#### Design decisions

- **One line per template, not a helper function call**: templates are shell-mode, not Claude code. A single `mantle stage-begin <name>` is self-documenting and trivial to review in diff.
- **Stage names match cost-policy keys when available**: prevents drift between cost-reporting vs stage-attribution vocabularies. Non-cost-policy stages (standalone commands like `brainstorm`, `idea`) use the command slug — there's no second source of truth to match.
- **Skip list tolerated as judgement call**: `help.md` and friends do no LLM work; instrumenting them would add noise without signal. AC-06 says \"every LLM-invoking template\", not \"every template\".
- **Parity snapshot refresh is mechanical**: `--inline-snapshot=create` handles the rewrite; the review step catches unintended drift (new tools surfacing in `allowed-tools`, timestamps bleeding into the baseline, etc.).
- **No attempt to cover all 30 templates in one commit**: if the implementer uncovers an LLM-invoking template missing from the instrumented list, they add it with the same one-line edit + re-snapshot. Partial coverage defeats the purpose — all-or-skip per template.

## Tests

Parity harness coverage (`tests/parity/`) is the primary test for this story — AC-06 demands every edited template's parity snapshot reflect the new line.

Two additional tests:

### tests/parity/test_stage_begin_coverage.py (new file)

- **test_every_non_skipped_template_begins_with_stage_begin**: iterate every `.md` / `.md.j2` file under `claude/commands/mantle/`. Skip list is a module-level set matching the shape doc (`help`, `resume`, `status`, `add-issue`, `add-skill`, `bug`, `inbox`, `query`). For each non-skipped template, read the file and assert that `mantle stage-begin ` appears before any other `mantle ` command-line call in the file. Fail with a directive message naming the missing template. This is the mechanical enforcement of AC-06.

Use plain `re.search` over the template body; keep the assertion message actionable: `f\"Template {name} is missing `mantle stage-begin` as its first shell call. Either add it or move {name} into the skip list in this test's module-level set.\"`

- **test_skip_list_templates_have_no_stage_begin**: symmetric check — every name in the skip list MUST NOT contain `mantle stage-begin`. Catches drift where a skipped template accidentally gets instrumented (would pollute telemetry with meaningless marks).

Both tests live under `tests/parity/` next to the existing parity tests; they protect the cross-template invariant the parity snapshots can't assert at the integrated-command level.

#### Test fixture requirements

- No tmp_path, no mocks — tests read the real `claude/commands/mantle/` directory on disk. This is deliberate: the tests are codebase-level policy tests, not unit tests.
- Use `Path(__file__).resolve().parents[2] / 'claude' / 'commands' / 'mantle'` to locate the directory (mirrors `tests/parity/test_prompt_coverage_policy.py` line 152).

## Verification against issue ACs

- **ac-06**: directly enforced by `test_every_non_skipped_template_begins_with_stage_begin` + `test_skip_list_templates_have_no_stage_begin`; parity snapshots of the 3 INTEGRATED templates are refreshed.
- **ac-08** (`just check` passes): implicit — all edits stay within ruff/ty/pytest-clean boundaries.