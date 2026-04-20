---
issue: 80
title: flip-ac --pass flag errors; verify.md drives users into the broken path
approaches:
- (a) Fix cyclopts binding so --pass is accepted
- (b) Drop --pass from verify.md and document the bare default form
chosen_approach: (a) Fix cyclopts binding so --pass is accepted
appetite: small batch
open_questions:
- None
author: 110059232+chonalchendo@users.noreply.github.com
created: '2026-04-20'
updated: '2026-04-20'
updated_by: 110059232+chonalchendo@users.noreply.github.com
tags:
- type/shaped
- phase/shaping
---

## Context

`verify.md` tells agents to run `mantle flip-ac --issue N --ac-id X --pass`, but cyclopts rejects `--pass` with `Unknown option: "--pass"`. Reproduced live on 2026-04-20.

Root cause: `src/mantle/cli/main.py:965-971` uses `Parameter(name="--pass/--fail", ...)`. Cyclopts does NOT interpret slash-pair syntax in `name` as a bool-pair alias; it generates `--no-pass` as the negation and `--pass` itself is never bound. `--help` confirms: it lists `--pass/--fail` on line one and `--no-pass/--fail` on line two. `--fail` happens to work because cyclopts interpreted the raw string as producing a literal `--fail` alias. The correct cyclopts API is `Parameter(name="--pass", negative="--fail", ...)` — `negative` is a first-class kwarg for boolean-pair negation.

## Approaches

### (a) Fix cyclopts binding — CHOSEN

Change `flip_ac_command`'s `passes` parameter from `name="--pass/--fail"` to `name="--pass", negative="--fail"`. Add a CLI-path test that invokes the app with `--pass` and asserts success.

- **Appetite:** small batch
- **Tradeoffs:** 1-line production change; aligns CLI with existing verify.md prose; help text becomes unambiguous.
- **Rabbit holes:** None — cyclopts `negative=` is documented first-class.
- **No-gos:** Does not touch any other CLI command; does not restructure the `passes`/`waive` relationship; does not touch `core/`.

### (b) Drop --pass from verify.md — REJECTED

Edit `claude/commands/mantle/verify.md` to show the bare default form `mantle flip-ac --issue N --ac-id X` instead of `--pass`. Optionally also remove `--pass` from the CLI display.

- **Appetite:** small batch (same as A).
- **Rejected because:** `--help` would still display `--pass` as an option the user could try; ergonomics remain inconsistent with `cli-design-best-practices`. A leaves the cleaner invariant: the flag shown in help == the flag the CLI accepts.

## Code design

### Strategy

- Edit `src/mantle/cli/main.py` at the `passes` `Annotated[bool, Parameter(...)]` binding. Replace `name="--pass/--fail"` with `name="--pass", negative="--fail"`. Default `= True` stays.
- Add one new test in `tests/cli/test_issues.py` (TestRunFlipAc class or a new TestFlipAcCli class): construct an issue, invoke `main_module.app("flip-ac --issue 1 --ac-id ac-01 --pass --path <tmp>")` and assert the criterion is now `passes=True`. Also cover `--fail`. This is the piece the existing tests miss — they all call `run_flip_ac(...)` directly, bypassing cyclopts.
- `verify.md` prose already uses `mantle flip-ac --issue {NN} --ac-id <ac-id> --pass`; no changes required.

### Fits architecture by

- Stays inside the `cli` slice — no `core/` changes, respecting the import-linter boundary (`core` never imports from `cli`; this doesn't reverse it).
- Uses cyclopts's first-class `negative=` parameter as documented in the `cyclopts` vault skill.
- Follows `cli-design-best-practices`: named flag + `--no-`/paired negation, consistency between `--help` output and documented usage.

### Does not

- Does not change `run_flip_ac` signature or semantics (ac-02: `--fail` still works).
- Does not touch `list-acs` or `migrate-acs`.
- Does not change `waive`/`reason` handling.
- Does not rewrite verify.md prose (already correct under approach A).
- Does not add end-to-end subprocess tests — the in-process `app("...")` invocation exercises the cyclopts binding which is the missing coverage.

## Open questions

None — root cause and fix verified against the cyclopts Parameter signature.
