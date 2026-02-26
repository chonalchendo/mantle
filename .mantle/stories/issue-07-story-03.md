---
issue: 7
title: CLI revision commands and main.py wiring
status: pending
failure_log: null
tags:
  - type/story
  - status/pending
---

## Implementation

Add CLI commands for revising product and system designs. Each wraps its core update function with Rich output and error handling. Wire both into `cli/main.py`.

### src/mantle/cli/product_design.py (modify)

#### New function

- `run_revise_product_design(*, vision, principles, building_blocks, prior_art, composition, target_users, success_metrics, change_topic, change_summary, change_rationale, project_dir=None) -> None` — Call `product_design.update_product_design()`. Print Rich confirmation with the change topic and decision log path. Handle `FileNotFoundError` by printing warning that directs user to `/mantle:design-product` and raising `SystemExit(1)`.

#### Output format

```
Product design revised in .mantle/product-design.md

  Change:   <change_topic>
  Decision: <decision_log_path.name>

  Next: review the revision in .mantle/product-design.md
```

On missing document:
```
Warning: product-design.md does not exist. Run /mantle:design-product first.
```

### src/mantle/cli/system_design.py (modify)

#### New function

- `run_revise_system_design(*, content, change_topic, change_summary, change_rationale, project_dir=None) -> None` — Call `system_design.update_system_design()`. Print Rich confirmation. Handle `FileNotFoundError` by printing warning that directs user to `/mantle:design-system` and raising `SystemExit(1)`.

#### Output format

```
System design revised in .mantle/system-design.md

  Change:   <change_topic>
  Decision: <decision_log_path.name>

  Next: review the revision in .mantle/system-design.md
```

On missing document:
```
Warning: system-design.md does not exist. Run /mantle:design-system first.
```

### src/mantle/cli/main.py (modify)

Add two new commands:

**`save-revised-product-design`** with cyclopts parameters:
- `--vision` (str, required)
- `--principles` (tuple[str, ...], required, repeatable)
- `--building-blocks` (tuple[str, ...], required, repeatable)
- `--prior-art` (tuple[str, ...], required, repeatable)
- `--composition` (str, required)
- `--target-users` (str, required)
- `--success-metrics` (tuple[str, ...], required, repeatable)
- `--change-topic` (str, required)
- `--change-summary` (str, required)
- `--change-rationale` (str, required)
- `--path` (Path | None, default None)

Import `from mantle.cli import product_design` and delegate.

**`save-revised-system-design`** with cyclopts parameters:
- `--content` (str, required)
- `--change-topic` (str, required)
- `--change-summary` (str, required)
- `--change-rationale` (str, required)
- `--path` (Path | None, default None)

Import `from mantle.cli import system_design` and delegate.

## Tests

- **run_revise_product_design**: prints "Product design revised" on success
- **run_revise_product_design**: prints change topic in output
- **run_revise_product_design**: prints decision log filename in output
- **run_revise_product_design**: warns and raises `SystemExit(1)` on missing document
- **run_revise_product_design**: warning mentions `/mantle:design-product`
- **run_revise_product_design**: defaults to cwd when `project_dir` is None
- **run_revise_system_design**: prints "System design revised" on success
- **run_revise_system_design**: prints change topic in output
- **run_revise_system_design**: prints decision log filename in output
- **run_revise_system_design**: warns and raises `SystemExit(1)` on missing document
- **run_revise_system_design**: warning mentions `/mantle:design-system`
- **CLI wiring**: `mantle save-revised-product-design --help` exits 0
- **CLI wiring**: `mantle save-revised-system-design --help` exits 0
