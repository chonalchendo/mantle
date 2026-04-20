---
issue: 78
title: Mechanical enforcement of core/ → cli/api import-direction invariant
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-20'
confidence_delta: '+1'
tags:
- type/learning
- phase/reviewing
---

## What went well

- **Approach selection held up end-to-end.** Shaping picked import-linter contracts over ast-walker and ruff-plugin on AC4 ("data-driven, extensible"); implementation confirmed the choice — one forbidden contract in pyproject.toml, zero bespoke code.
- **Single cohesive story was the right granularity.** Dep + config + wiring + test + docs landed in one commit (c58d216). Splitting would have left intermediate broken states (dep added but not wired, config without a test, etc.). Repeat this pattern for wiring-heavy issues where no piece is useful without the others.
- **Skill-driven shaping paid off.** The import-linter skill was authored just-in-time during this issue and immediately flagged two anti-patterns that made it into the shaped doc: contract "name" must be editorial (not `forbidden_1`), and contracts over `tests.*` as source_modules are wrong. Both held in implementation.
- **Live probe matched the test.** Verification confirmed lint-imports catches a real `from mantle.cli` inside core/, not just the fixture scenario.

## Harder than expected

- **import-linter Python API is under-documented.** The intuitive entry point (`importlinter.application.use_cases.lint_imports`) raises `KeyError: 'USER_OPTION_READERS'` without a manual `importlinter.configuration.configure()`. The CLI entry point (`importlinter.cli.lint_imports`) bootstraps configuration at import time and is the supported integration surface as of 2.11. Captured in story-1 learning.
- **INI vs TOML for the test fixture.** Flat `[importlinter]` + `[importlinter:contract:<id>]` INI sections parse fine in 2.11 — no need to switch to TOML for ad-hoc fixtures. Shaping had assumed TOML.

Neither was a shaping failure — they're the kind of detail only implementation surfaces. Shaping correctly pre-flagged "subprocess-vs-API for the test" as a rabbit hole.

## Wrong assumptions

- **AC5 (CONTRIBUTING.md) turned out to be mis-scoped.** CLAUDE.md is already the canonical contributor doc and is auto-loaded by Claude Code, so a separate CONTRIBUTING.md would have split the documentation surface. The shaped doc caught this before implementation and routed the docs into CLAUDE.md instead. Future ACs mentioning CONTRIBUTING.md should be interpreted as "the place contributors read," not a literal filename.
- **Default `lint-imports` output is probably sufficient for agent remediation.** AC2 asked for "remediation steps formatted for agent injection" — initially read as "write a custom `render_broken_contract`." On reflection, default output already names file, forbidden module, and contract name. Deferred the custom contract type until a real agent run fails to self-correct; if that never happens, the follow-up is never needed (YAGNI).

## Recommendations

- **Favour bundled stories for wiring-heavy issues.** When every piece (dep/config/wiring/test/docs) is a pre-requisite of the others, splitting just creates broken intermediate states. Save multi-story splits for issues where each story independently ships user-visible behaviour.
- **When picking a 3rd-party integration with a Python API, verify the actual entry point during shaping research, not implementation.** One quick `grep`/`help()` against the installed package would have caught the CLI-vs-application distinction upfront. For future issues that lean on a library's programmatic interface, add "confirm entry point by running `help()`" to shaping.
- **Defer output-polish ACs until real agent feedback.** AC2-style "shaped for downstream agent consumption" can almost always start with the tool's default output. Only invest in custom formatting when a real agent run demonstrates the default is insufficient. File the follow-up reactively, not proactively.
- **Extend with another contract, not another tool.** When the next architectural invariant lands (e.g. "cli may not import tests.fixtures", "no-skills-imports-core"), append a `[[tool.importlinter.contracts]]` block. No new dependency, no new test infrastructure — that's the payoff of the data-driven choice.
- **Adding a new vault skill inside a build cycle works.** The import-linter skill was authored mid-build and immediately guided shaping. If a shaping session hits a library-specific question with no existing skill, authoring one is cheap and compounds.