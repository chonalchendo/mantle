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
prices:
  opus:
    input: 15.00
    output: 75.00
    cache_read: 1.50
    cache_write: 18.75
  sonnet:
    input: 3.00
    output: 15.00
    cache_read: 0.30
    cache_write: 3.75
  haiku:
    input: 0.80
    output: 4.00
    cache_read: 0.08
    cache_write: 1.00
tags:
  - type/config
---

## Cost Policy

Per-stage model defaults for `/mantle:build`. Three presets:

- **budget** — cheapest viable path. Sonnet for shape/plan/verify; Haiku for mechanical stages.
- **balanced** (default) — Opus where reasoning compounds (shape), Sonnet everywhere else, Haiku on the trivially-mechanical end.
- **quality** — Opus on everything that writes code or makes design decisions. Sonnet only on mechanical finish-line stages.

## Prices

Token prices in USD per million tokens. Current rates as of 2026-04-24
(Anthropic Claude 3 family). **Refresh these at measurement time** from
Anthropic's public pricing page (<https://www.anthropic.com/pricing>).

| Model  | Input  | Output | Cache read | Cache write |
|--------|--------|--------|------------|-------------|
| opus   | 15.00  | 75.00  | 1.50       | 18.75       |
| sonnet | 3.00   | 15.00  | 0.30       | 3.75        |
| haiku  | 0.80   | 4.00   | 0.08       | 1.00        |

## How to use

Select a preset in `.mantle/config.md` frontmatter under a `models:` block:

    models:
      preset: balanced
      overrides:
        implement: opus    # escape hatch for a specific stage

Overrides beat preset beat hardcoded fallback.
