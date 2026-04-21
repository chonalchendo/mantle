---
issue: 84
title: Model-tier config with measured defaults
approaches:
- Preset + overrides (chosen)
- Flat per-stage (considered)
chosen_approach: Preset + overrides
appetite: medium batch (1 week)
open_questions:
- Does mantle install copy cost-policy.md into existing projects idempotently, or
  does the user run a new command explicitly? Probably the former (existing pattern)
  - confirm during plan-stories.
- Claude Code Agent model parameter accepts model IDs like claude-sonnet-4-6 - confirm
  the exact strings the policy doc should encode, and whether Haiku is passable as
  claude-haiku-4-5-20251001 or a shorter alias.
- For ac-04, dollar-cost calculation needs per-model token prices. Hardcode in a table
  in the baseline report template, or read from a config? Deferring to plan-stories.
- Should mantle model-tier be a new CLI subcommand, or should build.md call a Python
  one-liner via mantle dispatcher? Prefer the subcommand for testability.
author: 110059232+chonalchendo@users.noreply.github.com
created: '2026-04-21'
updated: '2026-04-21'
updated_by: 110059232+chonalchendo@users.noreply.github.com
tags:
- type/shaped
- phase/shaping
---

## Context — scope redesign

Issue 84 as originally written was an umbrella programme bundling four threads: model routing defaults, context budgeting, AI-led review/retrospective, and a policy doc. Shaping surfaced scope creep each time a question was asked (fold 75 in, add A/B harness, prune all pipeline prompts, restructure .mantle/), ending at ~3–4 weeks for a declared 1–2 week appetite. A first-principles pass identified the dominant lever: model tier, because Opus-4.7 is ~5x Sonnet on per-token cost and the pipeline defaults to Opus on every stage regardless of whether the stage needs Opus-grade reasoning.

The arithmetic:
- Model tier swap on mechanical stages: ~5x cost reduction, 2-3x speed-up.
- Prompt token pruning (second thread): ~30% input-token ceiling → ~6% total cost (output dominates on agentic runs).
- .mantle/ restructure: ~0% cost impact (cognitive-load only).

Conclusion: ship only the model-tier thread in this issue. The other concerns become their own narrow issues (listed under "Deferred to follow-up issues" in the issue body).

## Approach evaluation — config surface shape

Two genuine options for how the per-stage model config looks on disk.

### Approach A — Preset + overrides (chosen)

```yaml
# .mantle/config.md frontmatter
models:
  preset: balanced
  overrides:
    implement: opus
```

**Tradeoffs:** ergonomic common case (one knob); overrides as escape hatch; preset updates in cost-policy.md propagate automatically. Cost: config does not self-describe — reader cross-references cost-policy.md to see which models actually resolve.

**Rabbit holes:** resolution precedence must be unambiguous (overrides beat preset beat fallback). Pydantic validator should reject unknown stage keys in overrides so typos fail fast rather than silently falling back.

**No-gos:** does not validate model name strings against a known model list — that is Claude Code's responsibility at agent-spawn time.

### Approach B — Flat per-stage (considered, not chosen)

```yaml
models:
  shape: opus
  plan_stories: sonnet
  implement: sonnet
  ...
```

Presets documented as copy-paste templates in cost-policy.md.

**Why not chosen:** no indirection is appealing, but the common case (try a preset) costs the user seven lines to copy. Preset updates never propagate. Violates pull-complexity-downward — each project that wants to track preset improvements must manually sync.

## Code design

### Strategy

**New file: .mantle/cost-policy.md** — documentation plus machine-readable preset definitions.
- Frontmatter carries the preset-to-per-stage-model map so Python can parse it without prose parsing.
- Body contains one paragraph of rationale per preset.
- Created by mantle init from a template in vault-templates/cost-policy.md (new) on fresh installs; existing projects get it via mantle install running a one-time copy if the file is absent.

```yaml
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
---
```

**Extended: core/project.py** — add load_model_tier(project_root: Path) -> StageModels that:
1. Reads config.md frontmatter via existing read_config().
2. Reads cost-policy.md frontmatter to resolve the preset.
3. Applies per-stage overrides.
4. Returns a typed StageModels Pydantic model (new, colocated in core/project.py for proximity to read_config).

Signature sketch:

```python
class StageModels(pydantic.BaseModel, frozen=True):
    shape: str
    plan_stories: str
    implement: str
    simplify: str
    verify: str
    review: str
    retrospective: str

def load_model_tier(project_root: Path) -> StageModels: ...
```

Fallback: if cost-policy.md is absent (legacy projects), fall back to the balanced preset hardcoded as a module-level constant. This mirrors the existing missing-config fallback pattern from issue 83's learning.

**CLI wiring: cli/config.py** — new mantle model-tier subcommand (or extend an existing helper) that prints the resolved StageModels as JSON. Used by build.md at orchestration time.

**Prompt wiring: claude/commands/mantle/build.md** — Step 3 (or a new Step 3.5) reads the active tier via mantle model-tier --json and records the result in the build conversation. Each Task / Agent spawn in Steps 4-8 passes the corresponding stage's model via the Agent model parameter.

**Measurement for ac-04: no new CLI.** core/telemetry.py already parses Claude Code session JSONL into per-turn Usage records. The before/after measurement is a two-step manual procedure scripted into the story:
1. Run /mantle:build NN once on Opus-default. Parse the resulting session JSONL via the existing telemetry module. Record wall-clock seconds from time and dollar cost from token counts times known Claude prices.
2. Run /mantle:build NN once on balanced. Same parsing.
3. Write .mantle/telemetry/baseline-DATE.md by hand (or with a thin shell template) comparing the two runs.

The telemetry folder is introduced in this issue (empty except for the baseline report). No other artefact is moved into it — that is the deferred .mantle/ restructure issue.

### Fits architecture by

- **Honours core/ never imports from cli/ or claude/.** load_model_tier lives in core/project.py; the CLI wrapper is thin. Enforced by the existing import-linter contract in pyproject.toml.
- **Extends the read_config pattern.** load_model_tier is a typed layer on top of the existing raw-dict loader — no replacement, no migration. Fits the deep-module-over-shallow guidance in software-design-principles.
- **Matches verification-strategy precedence pattern.** build.md Step 8 already reads config.md for a per-project override and falls back to introspection. The new model-tier read follows the same precedence: per-config overrides beat policy-doc preset beat hardcoded fallback.
- **Fallback behaviour mirrors issue 83's learning.** If cost-policy.md is absent (legacy project), load_model_tier returns the hardcoded balanced preset rather than raising — catches the missing-config case at the loader boundary, not at every call site.
- **cost-policy.md placement.** Lives at .mantle/cost-policy.md (alongside product-design.md, system-design.md, config.md) — it is project-level configuration data, not telemetry. Distinct from the new .mantle/telemetry/ folder.

### Does not

**Derived from ACs:**
- Does not prune any build-pipeline prompts. Pruning is deferred to its own issue.
- Does not consolidate /mantle:review and /mantle:retrospective. Separate issue.
- Does not build an A/B harness. One manual before/after measurement is enough to validate the default choice; automated harness is deferred to issue 75 (kept open for that purpose).
- Does not move sessions/, builds/, learnings/ under .mantle/telemetry/. Restructure is a breaking change deferred to its own issue.
- Does not count tokens in build-pipeline prompts — measurement is wall-clock seconds and dollar cost per build, not per-prompt tokens.

**Derived from architecture boundaries:**
- Does not validate model-name strings against a known model list — that is Claude Code's job at agent-spawn time.
- Does not change the Agent-subagent spawning primitive in implement.md — the per-stage model is passed via the existing Agent model parameter.
- Does not introduce a new top-level Python module (core/config.py would be a shallow split from core/project.py — the existing owner).
- Does not gate build.md execution on the presence of cost-policy.md — legacy projects without it still work via the hardcoded balanced fallback.
- Does not persist past measurement runs in a structured database. .mantle/telemetry/baseline-DATE.md is a markdown file; future analysis can read the folder directly if needed.

## Side-effect impact scan

Adds new file .mantle/cost-policy.md on mantle init; existing projects get it on next mantle install via idempotent copy. Adds reads in build.md before agent spawns. Adds the .mantle/telemetry/ directory. No existing file is deleted or relocated. No state-machine transition is added. No hook is added.

Ordering dependency: build.md's model-tier read must happen before any agent spawn. Currently Step 3 (Load skills) does not spawn agents but Step 4 (Shape) can. The tier read slots in at the start of Step 3 (renamed Load skills and model tier) or as a new Step 2.5. Either way, the read is a cheap subprocess call on the CLI.