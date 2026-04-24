---
issue: 89
title: Pricing model + load_prices in core/project + cost-policy frontmatter
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a Mantle maintainer, I want a single canonical home for model prices inside `cost-policy.md` so that the A/B harness can compute real dollar figures without a separate config file or hardcoded rates.

## Depends On

None — independent (foundation for story 2).

## Approach

Follow the existing `StageModels` pattern in `core/project.py`: a frozen pydantic model plus a top-level loader that reads the `cost-policy.md` YAML frontmatter, identical to how `_load_presets()` already works. Extend the bundled `vault-templates/cost-policy.md` and the repo's own `.mantle/cost-policy.md` with a new `prices:` block. No new reader code path — reuses `_read_frontmatter_and_body()`.

## Implementation

### src/mantle/core/project.py (modify)

- Add a new pydantic model after `StageModels`:

  ```python
  class Pricing(pydantic.BaseModel, frozen=True):
      input: float
      output: float
      cache_read: float
      cache_write: float
  ```

  Units: USD per million tokens. Frozen — matches `StageModels` posture.

- Add `load_prices(project_root: Path) -> dict[str, Pricing]`. Reads `cost-policy.md` frontmatter via existing `_read_frontmatter_and_body()`, pulls `frontmatter["prices"]` as a `{model_name: {input, output, cache_read, cache_write}}` mapping, validates each value through `Pricing.model_validate(...)`, returns the resulting dict. If `cost-policy.md` is missing, raise `FileNotFoundError`. If the `prices:` key is absent, raise `KeyError("cost-policy.md has no 'prices' block")`. If a per-model entry fails validation, let pydantic's `ValidationError` propagate.

- Export `Pricing` and `load_prices` by placing them in the Public API section (above the `# ── Internal helpers ──` divider).

#### Design decisions

- **Keep `Pricing` in `project.py` alongside `StageModels`**: both are config-shaped value objects loaded from `cost-policy.md`. Putting `Pricing` in `ab_build.py` would force `core/project.py` to depend on `core/ab_build.py`, which reverses the layering.
- **Return `dict[str, Pricing]`, not a single `Pricing`**: prices differ per model (opus vs sonnet vs haiku). Callers look up by the `model` string on each `StoryRun`.
- **No fallback**: unlike `StageModels`, a missing prices block is a hard error — the A/B harness cannot compute cost without rates and silently returning zeros would violate AC-03 (no placeholder sentinels).

### vault-templates/cost-policy.md (modify)

Add a `prices:` block to the frontmatter with current published Anthropic rates as of 2026-04-24. Add `opus`, `sonnet`, `haiku` entries with `{input, output, cache_read, cache_write}` fields. Keep keys in kebab-or-snake-case consistent with existing frontmatter style. Update the body with a short `## Prices` section noting that values are dollars per million tokens and that users should refresh them from Anthropic's pricing page at measurement time.

### .mantle/cost-policy.md (modify)

Mirror the `prices:` block added to `vault-templates/cost-policy.md` so the local repo's own policy loads without error. This is a data-only edit — no code change.

## Tests

### tests/core/test_project.py (modify)

- **test_load_prices_returns_per_model_pricing**: given a `cost-policy.md` with a `prices:` block containing `opus`, `sonnet`, and `haiku` entries, `load_prices()` returns a dict with those three keys, each value is a `Pricing` instance, and the numeric fields round-trip exactly.
- **test_load_prices_raises_when_cost_policy_missing**: with no `cost-policy.md` under `tmp_path/.mantle/`, `load_prices()` raises `FileNotFoundError`.
- **test_load_prices_raises_when_prices_block_absent**: given a `cost-policy.md` with a `presets:` block but no `prices:` key, `load_prices()` raises `KeyError` whose message mentions `'prices'`.
- **test_load_prices_validates_numeric_fields**: given a `cost-policy.md` whose `prices.opus.input` is a string `"not-a-number"`, `load_prices()` raises `pydantic.ValidationError`.
- **test_bundled_vault_template_has_prices_block**: read the bundled `vault-templates/cost-policy.md` (via `resources.files("mantle").joinpath(...)`) and assert its parsed frontmatter has a non-empty `prices` mapping — guards against the template drifting from the loader contract.

Fixture requirements: write `cost-policy.md` under `tmp_path / ".mantle"` with handcrafted YAML frontmatter. No mocks needed — fully filesystem-local.