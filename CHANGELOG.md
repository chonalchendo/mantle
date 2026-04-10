# Changelog

All notable changes to Mantle are documented here. Format loosely follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow [SemVer](https://semver.org/).

## [0.12.0] — 2026-04-10

### Changed
- **Global-mode detection by directory existence** (#47). `resolve_mantle_dir` now checks whether `~/.mantle/projects/<identity>/` exists instead of reading a `storage_mode` field from `.mantle/config.md`. After `migrate-to-global`, the project directory contains no `.mantle/` folder at all — honouring the zero-footprint contract. Git worktrees inherit global context automatically via shared `project_identity()`.
- `migrate_to_global` no longer rebuilds a stub `.mantle/config.md`; it simply removes the local directory entirely.
- Removed orphaned `_update_config_at` helper and dead `storage_mode` config writes from `core/migration.py`.

### Fixed
- Build pipeline verify agent now calls `transition-issue-verified` before reporting, so the issue reaches `verified` status without manual intervention during review.

## [0.11.1] — 2026-04-09

### Fixed
- Save review result **before** the transition to `approved` so feedback is never lost when the review succeeds (#46).
- Decoupled archive side effects from `save-learning` — archiving now runs on `transition-to-approved`, so re-running `save-learning` mid-pipeline no longer orphans files.

## [0.11.0] — 2026-04-09

### Added
- `mantle where` CLI command — prints the resolved `.mantle/` location for the current project (#44).
- Global-mode sweep across all `/mantle:*` prompts so every command resolves `.mantle/` via `resolve_mantle_dir` instead of assuming a local path (#44).
- Archive scan in `next_issue_number` so issue IDs remain monotonic after issues are archived (#45).

## [0.10.0] — 2026-04-07

### Added
- **Global storage mode** (#43). Store project context at `~/.mantle/projects/<repo-identity>/` instead of in-repo — useful when modifying `.gitignore` isn't desirable.
  - `mantle storage` and `mantle migrate-storage` CLI commands.
  - `resolve_mantle_dir` / `project_identity` core resolvers (git-remote-derived identity survives re-clones).
  - All core modules updated to route through the resolver.

## [0.9.0] — 2026-04-07

### Added
- **Review persistence** (#40). Review results are now saved to `.mantle/reviews/` and re-loadable; the new `/mantle:fix` command reads saved feedback and drives targeted fixes.
- **Scout command** (#35). `/mantle:scout` clones an external repo, analyzes it through your project's design lens, and saves a `ScoutReport`. Enforced read-only on the clone; scouts are indexed by `/mantle:query`.
- **Skill-gating per issue** (#36). `IssueNote.skills_required`, `--issue` flag on `compile`, `--skills-required` on `save-issue`, "Required reading" section injected into implement prompts.
- **Verify vs review** distinction documented, with a convention check to keep them from drifting (#39).

### Fixed
- Allow `implemented → implementing` transition as a valid rollback path (#37).
- `collect-issue-files` commit detection (#38).

## [0.8.0] — 2026-04-02 → [0.8.9] — 2026-04-06

This line landed the **knowledge engine**, several new capture commands, and a large prompt-hardening sweep.

### Added
- **Knowledge graph commands** (#32): core `knowledge` module + `DistillationNote`; CLI `save-distillation`, `list`, `load`; `/mantle:query` and `/mantle:distill` prompts.
- **Inbox** (#31): `/mantle:inbox` for ultra-low-friction idea capture, wired into `plan-issues` and the `build` pipeline.
- **Tag collection** (#33): `collect_all_tags` with source merging + `mantle list-tags` CLI.
- **Skill discovery improvements** (#30).
- **Structured project introspection** (#29): `mantle introspect-project`, structured first-use / evolution / build-alignment in the verify prompt.
- **Brainstorm command** (#27): `/mantle:brainstorm` — core module, `save-brainstorm` CLI, prompt.
- **Add-issue** (#28): single-issue capture slash command.
- **Implemented status + auto-transitions** (#34) wired into build and implement prompts.
- **Two-stage review + model selection** in implement, defaulting to Opus.
- **Task progress tracking** added to all multi-step commands.
- Agent discipline + anti-rationalization patterns across build, implement, verify, challenge, simplify prompts.

### Fixed
- `--version` flag now works (cyclopts App passed the package version).
- Undefined `recent_decisions` in the status template.

## [0.7.0] — 2026-03-29 → [0.7.17] — 2026-04-01

### Added
- `/mantle:refactor` command — structured, skill-driven refactoring pass.
- **Simplify step** in the build pipeline (between implement and verify), with a separate `/mantle:simplify` entry point.
- **Skill gap detection** across build, plan-stories, and implement — missing skills are auto-created in the pipeline.
- **Per-story learning extraction** and context selection in `implement`.
- **Sub-agents, task tracking, AskUserQuestion, learnings loop**; personas dropped in favor of direct instructions (Claude 4.x behaves better without role-play).
- **Tool allowlists, inline context injection, structured hooks** applied to prompts.
- **Memory freshness warnings** and analysis-block stripping.
- **Descriptive filenames** for issues, stories, shaped issues, and learnings (slugs capped at 30 chars).
- **Auto-commit `.mantle/` artifacts** after session logging.
- Auto-detected `skills_required` from issue and story content (#26).

### Fixed
- NameError in `update-skills`; issue file glob matching.
- Build pipeline steps are now mandatory and sequential.

## [0.6.0] — 2026-03-23 → [0.6.2] — 2026-03-29

### Added
- **`/mantle:build`** — full automated pipeline from shaped issue through verified code in one command (#25).
- **Approve-all** quick action in the review workflow.
- **Dynamic next-step routing** in workflow skills.
- Fresh-context hints in build and implement commands.

## [0.5.0] — 2026-03-03 → [0.5.2] — 2026-03-05

### Added
- **`/mantle:verify`** — project-specific verification against acceptance criteria with auto-detected test/lint/check commands (#15).
- **`/mantle:review`** — human review workflow with pass/fail checklist and status transitions (#16).
- **`/mantle:simplify`** — post-implementation quality gate (#24).
- Enhanced Claude Code integration: named agents, permissions, dynamic context.

### Fixed
- Removed hardcoded tooling from `story-implementer` and implement command.
- Deduplicated transition functions; simplified CLI tests.

## [0.4.0] — 2026-03-02 → [0.4.2] — 2026-03-03

### Added
- **Story planning** (#12): core module, CLI, and `/mantle:plan-stories` command.
- **`/mantle:plan-issues`** — vertical-slice issue planning.
- **`/mantle:bug`** — structured bug capture.
- **`/mantle:implement`** — replaced subprocess orchestration with native Agent-based implementation (#12).
- **Skill graph extensions** (#21): stubs, tags, compilation, stub detection.

### Fixed
- Slugified wikilinks so Obsidian resolves to existing files.
- Project notes now placed under `projects/` in the vault, not the vault root.
- `save-research` no longer clobbers state during `add-skill`.

## [0.3.0] — 2026-02-26 → [0.3.1] — 2026-02-26

### Added
- **`/mantle:adopt`** (#19) — reverse-engineer product and system design from an existing codebase.
- **`/mantle:design-product`** (#05) and **`/mantle:design-system`** (#06) with decision logging.
- **`/mantle:research`** (#18) — first-principles building-block validation.
- **Design revision** commands with decision logging (#07).
- Replaced the `hypothesis` idea model with `problem + insight`.
- Product design reframed through first-principles decomposition (#4).
- Research context auto-loaded in `design-product`.

### Changed
- Workflow reordered: research now runs **before** design.

## [0.2.0] — 2026-02-24

### Added
- **`/mantle:idea`** — idea capture module, CLI command, and Claude Code prompt.
- **`/mantle:challenge`** — challenge-session module, CLI, and prompt (#04).
- Issue-03 stories; schema versioning, CLI reference, foundation-gap cleanup.

## [0.1.0] — 2026-02-24

Initial public release.

### Added
- Package skeleton, CLI entry point, project standards.
- Development tooling: `justfile`, ruff, ty, pytest, prek.
- GitHub Actions workflows for CI and PyPI publishing (trusted publishers).
- **`mantle init`**, **`mantle init-vault`**, **`mantle install`** — bootstrap, vault, and Claude Code command installation.
- File hash manifest module (`plan_install` / `record_install`).
- `/mantle:help` command file.
- README with project overview and quick start.

[0.12.0]: https://github.com/chonalchendo/mantle/releases/tag/v0.12.0
[0.11.1]: https://github.com/chonalchendo/mantle/releases/tag/v0.11.1
[0.11.0]: https://github.com/chonalchendo/mantle/releases/tag/v0.11.0
[0.10.0]: https://github.com/chonalchendo/mantle/releases/tag/v0.10.0
[0.9.0]: https://github.com/chonalchendo/mantle/releases/tag/v0.9.0
[0.8.9]: https://github.com/chonalchendo/mantle/releases/tag/v0.8.9
[0.8.0]: https://github.com/chonalchendo/mantle/releases/tag/v0.8.0
[0.7.17]: https://github.com/chonalchendo/mantle/releases/tag/v0.7.17
[0.7.0]: https://github.com/chonalchendo/mantle/releases/tag/v0.7.0
[0.6.2]: https://github.com/chonalchendo/mantle/releases/tag/v0.6.2
[0.6.0]: https://github.com/chonalchendo/mantle/releases/tag/v0.6.0
[0.5.2]: https://github.com/chonalchendo/mantle/releases/tag/v0.5.2
[0.5.0]: https://github.com/chonalchendo/mantle/releases/tag/v0.5.0
[0.4.2]: https://github.com/chonalchendo/mantle/releases/tag/v0.4.2
[0.4.0]: https://github.com/chonalchendo/mantle/releases/tag/v0.4.0
[0.3.1]: https://github.com/chonalchendo/mantle/releases/tag/v0.3.1
[0.3.0]: https://github.com/chonalchendo/mantle/releases/tag/v0.3.0
[0.2.0]: https://github.com/chonalchendo/mantle/releases/tag/v0.2.0
[0.1.0]: https://github.com/chonalchendo/mantle/releases/tag/v0.1.0
