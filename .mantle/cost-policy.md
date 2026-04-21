---
presets:
  budget:
    shape: sonnet
    plan_stories: sonnet
    implement: haiku
    simplify: haiku
    verify: sonnet
    review: haiku
    retrospective: haiku
  balanced:
    shape: opus
    plan_stories: sonnet
    implement: sonnet
    simplify: sonnet
    verify: sonnet
    review: haiku
    retrospective: haiku
  quality:
    shape: opus
    plan_stories: opus
    implement: opus
    simplify: sonnet
    verify: sonnet
    review: sonnet
    retrospective: sonnet
tags:
  - type/config
---

## Cost Policy

Per-stage model defaults for `/mantle:build`. Three presets:

- **budget** — cheapest viable path. Sonnet for shape/plan/verify; Haiku for mechanical stages.
- **balanced** (default) — Opus where reasoning compounds (shape), Sonnet everywhere else, Haiku on the trivially-mechanical end.
- **quality** — Opus on everything that writes code or makes design decisions. Sonnet only on mechanical finish-line stages.

## How to use

Select a preset in `.mantle/config.md` frontmatter under a `models:` block:

    models:
      preset: balanced
      overrides:
        implement: opus    # escape hatch for a specific stage

Overrides beat preset beat hardcoded fallback.
