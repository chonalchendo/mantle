---
issue: 77
title: Machine-verifiable acceptance criteria with explicit pass/fail state
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-20'
confidence_delta: '+2'
tags:
- type/learning
- phase/reviewing
---

## What went well

- **Approach A held end-to-end.** Shaping chose "extend IssueNote + regenerate body on save + flip-ac/migrate-acs CLI" over a sidecar file or pure-regex approach. Every downstream step — stories, implementation, tests, verify — landed against that approach without churn. The `acceptance_criteria: tuple = ()` default as the back-compat escape hatch made it safe to ship story 1 (schema + gate) before story 2 (CLI + migration) ran against the live backlog.
- **2-story split was the right granularity.** Story 1 (pure core: schema, parse/render/flip helpers, IssueNote integration, transition gate) shipped as a testable foundation; story 2 (CLI wrappers, prompt wiring, live backfill) integrated it. Learnings handed off from story 1 → story 2 via `mantle save-learning` directly informed story 2's import convention and regex reuse. Contrast with issue 78 where one cohesive story was right — the distinguishing factor is whether intermediate state is coherent. Here story 1 ships a usable Python API with tests; the CLI layer is genuinely separable.
- **Migration round-trip is idempotent.** `parse_ac_section` strips both `ac-NN:` prefixes and trailing `(waived)` markers, so regen → parse → regen is a fixed point. Backfilling 74 archived issues produced zero data loss and a second `migrate-acs` run reports zero work.
- **Gate placement in `transition_to_approved` (not `transition_to_verified`) is the correct seam.** Verify flips per-criterion as evidence arrives; approval is the single chokepoint. Empty-tuple issues still approve cleanly, preserving back-compat.

## Harder than expected

- **Cyclopts `--pass/--fail` negation syntax doesn't work as the skill documentation implies.** `mantle flip-ac --issue N --ac-id X --pass` errored with "Unknown option: '--pass'" during verify — the default-true bool worked, and `--fail` worked, but explicit `--pass` didn't. Verify.md had already been wired to call `--pass`, so the prompt and CLI disagreed. Captured as issue 80; caught at verify-time, not implementation — the CLI unit tests didn't exercise the parsed-from-help form.
- **`mantle save-review-result` splits on `|` in AC text.** Issue 77's own AC 1 contained `passes: true|false` in backticks; the review-result parser took the first `|` as the status delimiter. Worked around by substituting "or" for `|` in the reviewer record; the underlying issue is a CLI-delimiter limitation pre-dating this issue.
- **Globally-installed `mantle` goes stale inside a build.** The new `list-acs`/`flip-ac`/`migrate-acs` commands only work via `uv run mantle` until the user runs `uv tool install --reinstall .`. The verify agent caught this but didn't fail over it; future issues introducing new CLI subcommands should either note the staleness in the build report or trigger an install refresh.
- **Story 1 → Story 2 learnings file naming.** The filename was `issue-77-story-1-acceptance-core-issu.md` (slug truncated from the title). Story 2's prompt had to do a "latest `issue-77-story-1*`" glob rather than predicting the exact filename — cheap friction, but a naming convention for per-story learnings would remove the glob.

## Wrong assumptions

- **Assumed cyclopts' `Parameter(name='--pass/--fail')` handled both flags symmetrically.** It handled `--fail` (sets False) and absent-flag (keeps default True) but treated `--pass` as unknown. The cyclopts skill's example code shows this syntax; the actual behaviour diverges. Next time a skill example is used verbatim, spot-check it against `tool --help` before baking it into a prompt.
- **Initially thought story 2 would need a backfill-only story separate from the CLI story.** Turned out the backfill is a one-shot `uv run mantle migrate-acs` at story-2 tail — not worth its own story. Story 2 absorbed it cleanly and the auto-commit hook captured 74 migrated files as a distinct chore commit.
- **Expected verify to skip flipping ACs on an issue whose status was `implemented`.** It actually flipped all seven during the verify agent run, which is exactly the behaviour we wanted. The iron law "NO pass WITHOUT evidence" held because each flip cited concrete evidence. Good — but it means the gate only blocks if somebody explicitly flips something to fail, not from default-false.

## Recommendations

- **Include a `tool --help` spot-check in any story that wires a new CLI command into a prompt.** Story 2 had prompt edits referencing `--pass` without ever running `mantle flip-ac --help`. A 10-second sanity check would have caught the cyclopts quirk.
- **When shipping a new CLI subcommand on master, follow-up with a `uv tool install --reinstall .` note in the build report.** Otherwise the global install quietly diverges from master until the next release.
- **Keep the "core story + integration story" pattern for schema-extension issues.** Extending a core Pydantic model + regenerating a derived view + gating a transition is a repeatable shape. Story 1 = pure module + model extension + gate; story 2 = CLI + prompts + one-shot backfill. Future shaping should recognise this shape and reach for it directly.
- **File an issue to stop `save-review-result` splitting on `|` inside backticked AC text.** Workaround today is to rewrite the criterion text; proper fix is a different delimiter (`\t` or an index-based form).
- **Gate on `transition_to_approved` is the right place.** Anyone adding more state-machine gates (e.g. "no approval while tests are red") should use the same pattern: raise a dedicated exception *before* `_transition_issue`, so the hook doesn't dispatch on a blocked transition.
- **Structured ACs now unlock richer `/mantle:patterns` and `/mantle:review` flows.** Worth filing a follow-up to have `/mantle:review` present per-AC `passes` / `waived` state directly from the frontmatter (today it does — but the prompt edits were conservative; it could lean harder on the structured data for a more informative checklist render).