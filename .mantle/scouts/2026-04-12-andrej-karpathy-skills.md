---
date: '2026-04-12'
author: 110059232+chonalchendo@users.noreply.github.com
repo_url: https://github.com/forrestchang/andrej-karpathy-skills
repo_name: andrej-karpathy-skills
dimensions:
- skill-authoring
- domain
tags:
- type/scout
---

# Scout Report: andrej-karpathy-skills

**Repository**: https://github.com/forrestchang/andrej-karpathy-skills
**Analyzed**: 2026-04-12
**Project context**: Mantle — AI workflow engine giving Claude Code persistent memory, idea validation, and structured product development.

---

## Executive Summary

The repo is tiny — a single Claude Code plugin/skill (`karpathy-guidelines`) plus CLAUDE.md/README.md/EXAMPLES.md (~750 lines total). Not a code project: no Python, CLI, tests, or architecture. Its sole artefact is a crisp 4-principle behavioural ruleset for LLM coding agents (Think Before Coding / Simplicity First / Surgical Changes / Goal-Driven Execution), derived from Karpathy's public observations. Signal quality for Mantle is medium-high but narrow: ideas overlap heavily with Mantle's existing Iron Laws / Red Flags / simplify / verify patterns, and the Claude Code plugin distribution model is a concrete packaging lesson Mantle has not yet exploited.

---

## Findings by Dimension

Architecture / Coding Patterns / Testing / CLI are not applicable — no executable code.

### Skill-authoring patterns

- **Single-file distilled skill** — Entire skill is one short SKILL.md with 4 named principles, each 3–5 bullet rules plus a one-sentence test. Relevant to Mantle's `skill-authoring` ethos. **Adapt** — use for future *behavioural* skills; keep reference skills longer-form.
- **"The test:" one-liner per principle** — Each principle ends with a falsifiable check (e.g. "Every changed line should trace directly to the user's request"). Mantle's Iron Laws lack self-check rubrics. **Adopt** — add falsifiable self-check lines to Iron Laws in build.md, simplify.md, implement.md.
- **Tradeoff disclosure up front** — "Tradeoff: these guidelines bias toward caution over speed." Mantle commands sometimes feel heavy-weight. **Adapt** — add tradeoff notes to heavyweight commands (build, shape-issue, plan-stories).

### Domain-specific features

- **Goal-Driven Execution transform table** — Converts imperative tasks ("Add validation") into verifiable goals ("Write tests for invalid inputs, then make them pass"). Mantle's plan-stories produces TDD specs but shape-issue/implement could sharpen. **Adopt** — bake imperative→verifiable transform into shape-issue.md / plan-stories.md.
- **Claude Code Plugin marketplace distribution** — Ships via `/plugin marketplace add` + `/plugin install`, globally across projects. Mantle installs via PyPI; a plugin layer would give global cross-project slash commands. Relevant to issue 41 (pattern query) and the multi-repo work scenario. **Adapt** — evaluate Claude Code plugin wrapper over the PyPI CLI.
- **Karpathy-anchored credibility framing** — README leads with practitioner quotes. **Skip** — narrative flourish, not structural.
- **"How to know it's working" observable signals** — Lists diff/PR signals that mean the guidelines are succeeding. Natural extension of `/mantle:retrospective` and `/mantle:patterns`. **Adapt** — add observable-signals section to retrospective prompt so learnings capture "what good looks like," not just regressions.

---

## Actionable Recommendations

### Adopt
- **Falsifiable self-check per Iron Law** (skill-authoring): Add a one-line "test:" check to each Iron Law across build.md, simplify.md, implement.md.
- **Imperative→verifiable-goal transform** (domain): Explicit step in shape-issue.md and plan-stories.md that rewrites imperative ACs into test-first form.

### Adapt
- **Single-file behavioural skill form** (skill-authoring): Use for Mantle's future behavioural skills.
- **Tradeoff disclosure** (skill-authoring): One-line "caution over speed" note on heavyweight commands.
- **Claude Code plugin distribution** (domain): Wrap `/mantle:*` + `.claude/skills/` as a plugin over PyPI CLI — addresses stale-global-install pain and multi-repo usage.
- **Observable-signals retrospective** (domain): Extend `/mantle:retrospective` to capture good-outcome signals, not only regressions.

### Skip
- **Karpathy credibility framing** (domain): Narrative device, no change needed.
- **Architecture / coding / testing / CLI**: Not present in repo.

---

## Backlog Implications

- Reinforces **issue 51 (contextual CLI errors with recommendations)** — the Goal-Driven Execution transform is the same shape (imperative failure → actionable next step); consider unifying the framing.
- Suggests a **new issue — Claude Code plugin distribution**: wrap slash commands + skills as installable plugin. Addresses stale-global-install pain (0.16.0 retrospective) and multi-repo work scenario in memory.
- Small enhancement to **issue 56 (lifecycle hook seam)**: falsifiable-test-per-rule fits lifecycle hooks — each hook declares a one-line post-condition.
- Reinforces **issue 41 (pattern query)** direction: observable good-outcome signals, not just failure modes.