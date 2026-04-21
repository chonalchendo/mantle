---
issue: 84
title: StageModels and load_model_tier in core/project.py
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a Mantle user on API billing, I want the build pipeline to resolve per-stage model choices from config and cost-policy, so mechanical stages can be routed to cheaper models without scattering that logic across every prompt.

## Depends On

Story 1 — reads `cost-policy.md` written by story 1's template.

## Approach

Add a typed loader layer on top of the existing `read_config` raw-dict pattern, following the same precedence model as `verify.load_strategy` (per-target override → config default → fallback). The new `load_model_tier` returns a frozen `StageModels` Pydantic record — frozen because the value flows through to `build.md` where any mutation would be a bug. The missing-config fallback pattern matches issue 83's learning ("add missing-config fallback at the loader, not at every call site").

## Implementation

### src/mantle/core/project.py (modify)

Add to the public API section, below `init_vault`:

1. **New constant** `_STAGE_NAMES: tuple[str, ...]` — the seven stages, single source of truth for stage validation:
   ```python
   _STAGE_NAMES: tuple[str, ...] = (
       "shape", "plan_stories", "implement",
       "simplify", "verify", "review", "retrospective",
   )
   ```

2. **Public Pydantic model** `StageModels(pydantic.BaseModel, frozen=True)` with one `str` field per stage (seven fields, names matching `_STAGE_NAMES`). Frozen so downstream prompts can treat it as immutable.

3. **Module-level constant** `_FALLBACK_STAGE_MODELS: StageModels` — the `balanced` preset values hardcoded (shape=opus, plan_stories=sonnet, implement=sonnet, simplify=sonnet, verify=sonnet, review=haiku, retrospective=haiku). Used when `cost-policy.md` is absent.

4. **Internal Pydantic model** `_ModelsConfig(pydantic.BaseModel)` for the `models:` block in `config.md`:
   ```python
   class _ModelsConfig(pydantic.BaseModel):
       preset: str = "balanced"
       overrides: dict[str, str] = pydantic.Field(default_factory=dict)

       @pydantic.field_validator("overrides")
       @classmethod
       def _validate_override_keys(cls, v: dict[str, str]) -> dict[str, str]:
           unknown = set(v) - set(_STAGE_NAMES)
           if unknown:
               msg = (
                   f"Unknown stage(s) in models.overrides: "
                   f"{sorted(unknown)}. "
                   f"Valid stages: {list(_STAGE_NAMES)}."
               )
               raise ValueError(msg)
           return v
   ```

5. **Public function** `load_model_tier(project_root: Path) -> StageModels` with this precedence:
   1. Try `read_config(project_root)` — if absent, return `_FALLBACK_STAGE_MODELS`.
   2. Extract the `models` sub-dict; if absent or empty, treat as `{}` (preset defaults to `balanced`, no overrides).
   3. Parse via `_ModelsConfig.model_validate(...)` — raises `pydantic.ValidationError` on unknown override keys (intentional — typos fail fast).
   4. Try to load `cost-policy.md` presets via a new helper `_load_presets(project_root) -> dict[str, dict[str, str]]` that reads the frontmatter. If `cost-policy.md` is absent, fall back to `{"balanced": _FALLBACK_STAGE_MODELS.model_dump()}`.
   5. Select preset by name; raise `KeyError` with a clear message if the preset isn't defined in `cost-policy.md`.
   6. Apply overrides dict on top of preset dict.
   7. Return `StageModels(**merged)`.

6. **Internal helper** `_load_presets(project_root: Path) -> dict[str, dict[str, str]]`:
   - Reads `cost-policy.md` frontmatter via `_read_frontmatter_and_body`.
   - Returns the `presets` field, or a dict containing only the hardcoded fallback's `balanced` entry if the file doesn't exist.
   - Catches `FileNotFoundError` only — other errors (malformed YAML) propagate.

#### Design decisions

- **_STAGE_NAMES as the single source of truth.** Both `StageModels` fields and `_ModelsConfig.overrides` validation reference it. Adding an eighth stage in the future means touching one constant, not three.
- **Frozen StageModels.** The value is consumed by `build.md` prompt (via `mantle model-tier --json` in story 3). An immutable record prevents accidental mutation if the loader is imported elsewhere later.
- **_ModelsConfig private, StageModels public.** The internal model exists only to validate the raw `models:` dict from config.md. Downstream code only needs the resolved stage map (`StageModels`) — so that's the only thing exported.
- **Fallback on FileNotFoundError, not on Exception.** Mirrors issue 83's learning ("add missing-config fallback at the loader") but keeps the fallback narrow. A malformed `cost-policy.md` should raise, not silently fall back — bad YAML is a bug.
- **Colocate in core/project.py.** The shaped doc explicitly rules out a new `core/config.py` module as a shallow split. `load_model_tier` extends the existing config-reader pattern in the same file.

## Tests

### tests/core/test_project.py (modify)

New test class `TestLoadModelTier`:

- **test_returns_balanced_fallback_when_no_config**: Empty `tmp_path` (no `.mantle/` at all) → `load_model_tier(tmp_path)` returns `StageModels` equal to `_FALLBACK_STAGE_MODELS`.
- **test_returns_balanced_fallback_when_no_cost_policy**: Call `init_project` then delete `cost-policy.md` → `load_model_tier` returns the hardcoded `_FALLBACK_STAGE_MODELS` (tests the `FileNotFoundError` branch in `_load_presets`).
- **test_resolves_preset_from_cost_policy**: Fresh `init_project` with no `models:` block in `config.md` → returns the `balanced` preset as defined in `cost-policy.md` (all 7 fields match the template).
- **test_resolves_named_preset**: `update_config(project_root, models={"preset": "budget"})` → returns the budget preset from `cost-policy.md` (`implement == "haiku"`, `shape == "sonnet"`).
- **test_overrides_beat_preset**: `update_config(..., models={"preset": "budget", "overrides": {"implement": "opus"}})` → `result.implement == "opus"`, `result.simplify == "haiku"` (untouched fields still come from preset).
- **test_unknown_override_key_raises**: `update_config(..., models={"preset": "balanced", "overrides": {"typoed_stage": "opus"}})` → `load_model_tier` raises `pydantic.ValidationError` containing the string `"typoed_stage"`.
- **test_unknown_preset_raises_key_error**: `update_config(..., models={"preset": "rocket_fuel"})` → raises `KeyError` with a message naming the bad preset.
- **test_stage_models_is_frozen**: Create any `StageModels` instance and attempt attribute assignment → raises `pydantic.ValidationError` (or `TypeError`, depending on Pydantic version — assert on instance type).
- **test_fallback_preset_matches_cost_policy_balanced**: `_FALLBACK_STAGE_MODELS` field values match the `balanced` preset in `vault-templates/cost-policy.md` (prevents drift between the template and the fallback constant).

Fixtures: reuse `_mock_git` autouse. Use `init_project` then `update_config` — no new helpers needed.
