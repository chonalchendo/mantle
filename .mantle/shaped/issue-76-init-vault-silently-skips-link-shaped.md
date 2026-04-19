---
issue: 76
title: init-vault silently skips linking when vault directory already exists
approaches:
- 'Core-level idempotency: init_vault skips mkdir when all four subdirs exist, still
  calls update_config, returns a flag indicating whether the vault was freshly created
  or pre-existing'
- 'CLI-level swallow: CLI catches FileExistsError and calls update_config itself'
chosen_approach: Core-level idempotency
appetite: small batch
open_questions: []
author: 110059232+chonalchendo@users.noreply.github.com
created: '2026-04-19'
updated: '2026-04-19'
updated_by: 110059232+chonalchendo@users.noreply.github.com
tags:
- type/shaped
- phase/shaping
---

## Chosen approach: Core-level idempotency

Make `core.project.init_vault` idempotent. When all four subdirectories (`skills`, `knowledge`, `inbox`, `projects`) already exist at the resolved vault path, skip the `mkdir` loop but still invoke `update_config(project_root, personal_vault=str(resolved))`. Signal the outcome to callers so the CLI can print a distinct message.

## Tradeoffs

**A — Core-level (chosen)**
- +: keeps `init_vault` semantically honest (idempotent linking is a real semantic, not a CLI workaround)
- +: future callers (tests, other CLIs, scripts) get the correct behaviour for free
- +: CLI stays a thin formatting layer — no exception-as-control-flow
- -: changes a function signature (adds a return value), so one callsite needs updating
- -: existing `FileExistsError`-raising semantics are removed; any script relying on them breaks (none found in tree)

**B — CLI-level swallow**
- +: isolated change, core untouched
- -: re-implements part of `init_vault`'s contract inside the CLI (call `update_config` manually)
- -: `init_vault` remains misleading (raises instead of linking), future callers re-hit the bug
- -: forces the CLI to know about core internals (that `update_config` is what it actually needed)

## Rabbit holes & no-gos

- Partial vault state (e.g., only `skills/` and `knowledge/` exist) is out of scope — ACs only require the all-subdirs-exist case.
- Configurable override when `personal_vault` already points elsewhere is out of scope — ACs require population, not conflict-detection.
- No migration of legacy config keys.

## Code design

### Strategy

- In `src/mantle/core/project.py::init_vault` (~line 314), replace the `FileExistsError` raise at line 336-338 with a branch: if all four subdirs exist, skip the `mkdir` loop; otherwise create them. In both branches, call `update_config(project_root, personal_vault=str(resolved))`.
- Change the return type from `None` to a small enum-like indicator. Cheapest: `bool` — `True` if the vault was newly created, `False` if linked to an existing vault. Update the docstring accordingly and drop the `FileExistsError` from the `Raises:` section.
- In `src/mantle/cli/init_vault.py::run_init_vault`:
  - Remove the `except FileExistsError` handler entirely.
  - Capture the boolean return and branch the success message:
    - Fresh vault: existing "Created personal vault at {path}" block with subdirs + tip.
    - Pre-existing vault: new message like "Linked existing vault at {path}" with a short note that config was updated.
- Per `cli-design-best-practices`: write success messages to the existing `rich.Console()` (project convention), keep exit code 0, and keep the messaging distinct so scripts can grep either phrase.
- Per `python-314`: no PEP 758 `except A, B:` changes needed here (only one exception class remains: `FileNotFoundError`). No new type-hint quoting needed.

### Tests (TDD)

Three new tests covering:
1. `test_init_vault_links_existing_vault` — given a path where all four subdirs pre-exist (created by another project), `init_vault` returns `False`, does not raise, and writes `personal_vault: <path>` to `.mantle/config.md`.
2. `test_init_vault_creates_fresh_vault` — unchanged behaviour regression: fresh path creates all four subdirs, writes config, returns `True`.
3. `test_cli_init_vault_linked_message` — CLI test that `run_init_vault` on a pre-existing path prints a "Linked existing vault" style message (not "Nothing to do") and populates config.

Multi-project integration test: spin up two `tmp_path` project roots, point both at the same vault path, and assert both `config.md` files contain `personal_vault`.

Use `tmp_path` (per CLAUDE.md test conventions) — no touching real vaults.

### Fits architecture by

- Respects `core/` → never imports from `cli/` (unchanged).
- CLI remains the presentation layer; core owns the state transition.
- Fits the `init_*` family's idempotency pattern — most mantle init commands should be safely re-runnable; this fixes a regression from that pattern.
- No system-design changes needed.

### Does not

- Does not validate or reject conflicting `personal_vault` values already in config (CLI config-edit responsibility, separate issue).
- Does not handle partial vault state (some but not all subdirs exist) — ACs are silent on this.
- Does not change the CLI argument surface (no new flags).
- Does not change how `update_config` serialises frontmatter.
- Does not affect any other `mantle init*` command.

## Acceptance criteria mapping

- AC1 "records personal_vault in config.md without raising" → Strategy bullet 1 (skip mkdir, still update_config) + test 1.
- AC2 "Linked existing vault" message → Strategy bullet 3 (CLI branch) + test 3.
- AC3 "fresh path still creates subdirs and links" → Strategy bullet 1 (fresh branch retained) + test 2.
- AC4 "multi-project share flow regression test" → integration test in plan above.