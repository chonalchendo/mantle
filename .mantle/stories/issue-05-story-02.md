---
issue: 5
title: CLI save-product-design command
status: pending
failure_log: null
tags:
  - type/story
  - status/pending
---

## Implementation

Add the `mantle save-product-design` CLI command that wraps `core.product_design.create_product_design()` with Rich output and error handling.

### src/mantle/cli/product_design.py

```python
"""Save-product-design command — capture product design in .mantle/product-design.md."""
```

#### Function

- `run_save_product_design(*, vision, features, target_users, success_metrics, genuine_edge, overwrite=False, project_dir=None) -> None` — Call `product_design.create_product_design()`, print Rich confirmation with vision and feature count, suggest `/mantle:design-system` as next step. Handle `ProductDesignExistsError` by printing warning and raising `SystemExit(1)`. Default `project_dir` to `Path.cwd()`.

#### Output format

```
Product design saved to .mantle/product-design.md

  Vision:   <vision>
  Features: <count>

  Next: run /mantle:design-system to define the how
```

On existing:
```
Warning: product-design.md already exists. Use --overwrite to replace.
```

### src/mantle/cli/main.py (modify)

Add `save-product-design` command with cyclopts parameters:

- `--vision` (str, required)
- `--features` (tuple[str, ...], required, repeatable)
- `--target-users` (str, required)
- `--success-metrics` (tuple[str, ...], required, repeatable)
- `--genuine-edge` (str, required)
- `--overwrite` (bool, default False)
- `--path` (Path | None, default None)

Import `from mantle.cli import product_design` and delegate.

## Tests

- **run_save_product_design**: prints "Product design saved" on success
- **run_save_product_design**: prints vision in output
- **run_save_product_design**: prints feature count in output
- **run_save_product_design**: prints next step mentioning `/mantle:design-system`
- **run_save_product_design**: warns and raises `SystemExit(1)` on existing
- **run_save_product_design**: `overwrite=True` succeeds when exists
- **run_save_product_design**: defaults to cwd when `project_dir` is None
- **CLI wiring**: `mantle save-product-design --help` exits 0 and mentions "vision"
