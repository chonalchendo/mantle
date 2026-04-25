# Changelog

All notable changes to Mantle are documented here. Format loosely follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow [SemVer](https://semver.org/).

## [0.23.0] — 2026-04-25

### Added
- **Prompt-layer golden-parity test harness** (#90) — new `tests/parity/` package captures normalized snapshots of the rendered `/mantle:*` command prompts so token-cut refactors fail loudly instead of silently shifting agent-visible content. `tests/parity/harness.py` exposes `run_prompt_parity(command, fixture, baseline)`; `normalize_prompt_output()` strips timestamps, session IDs, absolute paths, and git SHAs before comparison. Three commands are wired up at launch (`build`, `implement`, `plan-stories`) via per-command `test_<cmd>_parity.py` files; `test_prompt_coverage_policy.py` enumerates every `/mantle:*` command in the repo and fails CI if a new one lands without an `INTEGRATED` / `DEFERRED` classification. CLAUDE.md grows a "Prompt-parity harness" subsection covering scope, baseline capture (`uv run pytest --inline-snapshot=create`), accepting deliberate diffs (`--inline-snapshot=review`), and promoting `DEFERRED` → `INTEGRATED`.
- **Per-stage build telemetry** (#92) — a universal `mantle stage-begin <name>` CLI primitive appends a well-formed JSONL `StageMark` to `.mantle/telemetry/stages-<session_id>.jsonl`, giving every LLM-invoking `claude/commands/mantle/*.md` template a single line of opening instrumentation. `core/stages.py` defines the `StageMark` record and append helper; `core/telemetry.py` gains a sub-agent JSONL read path that walks `<parent_session>/subagents/agent-*.jsonl` and emits one `StoryRun` per sub-agent transcript, plus a `StageWindow` algorithm that attributes parent-session inline turns to the enclosing stage. `BuildReport` stays backward-compatible — existing `.mantle/builds/build-NN-*.md` files keep parsing — and per-stage rows now carry tokens, wall-clock seconds, and `cost_usd` resolved from `.mantle/cost-policy.md` prices. Roundtrip tests cover synthetic parent + `subagents/` + stages JSONL fixtures and a copy of build-90's real session directory; story-id is parsed from sub-agent description markers so per-story attribution survives partial logs.
- **Post-hoc A/B harness for build pipeline** (#89) — `mantle ab-build-compare <baseline.md> <candidate.md>` renders a stage-grouped delta report comparing two recorded build reports along tokens, wall-clock seconds, and dollar cost. `core/ab_build.py` defines `ComparisonRow`, `Comparison`, `BuildArtefacts`, `QualityStats`, `CostBreakdown` value objects plus pure `compute_cost`, `collect_quality`, `build_comparison`, `render_markdown` functions; the verifier rejects placeholder cells (`<fill>`, `TBD`). Pricing flows in via a new `Pricing` Pydantic model + `project.load_prices()` reading the `prices` block from `.mantle/cost-policy.md`, with full Anthropic model IDs resolved to tier-keyed prices so per-stage `cost_usd` is filled when the cost policy is present and gracefully degraded when it is not. The harness runs from outside `/mantle:build` (no nested-build invocation).

### Fixed
- **`token-audit` report snapshots are deterministic.** `core/token_audit.format_report` and `cli/audit_tokens.run_audit_tokens` accept a `today: date | None = None` kwarg defaulting to `date.today()`; tests pass a fixed date so the four inline snapshots that embed the report header date no longer drift with the calendar.

## [0.22.0] — 2026-04-24

### Fixed
- **Build telemetry writes real session UUIDs again** (#91) — the Claude Code `SessionStart` hook (`claude/hooks/session-start.sh`) now reads the hook's JSON stdin payload, extracts `session_id` via `jq` with a `python3` fallback, and writes it to `<project_dir>/.mantle/.session-id` atomically (mktemp + rename on the same filesystem). The whole block is fail-soft — TTY stdin, empty payload, missing `jq`, and non-JSON garbage all degrade to no-op without aborting the hook. Resolves 8 days of silent telemetry rot (`.mantle/builds/` had been recording the same stale UUID, `datetime.min` timestamps, and empty `stories:` lists since 2026-04-17) by finally honouring the documented `CLAUDE_SESSION_ID` → `.mantle/.session-id` resolution chain in `core/telemetry.py:current_session_id()`. Unblocks issue 89 (A/B harness needs real per-story telemetry) and lays groundwork for issue 85 (cross-repo session identity). Regression coverage: four new end-to-end tests in `tests/hooks/test_session_start.py` feed stdin payloads through the actual shell hook — happy path, `jq`-absent fallback, empty stdin, and malformed JSON.

## [0.21.0] — 2026-04-21

### Added
- **Model-tier config for `/mantle:build`** (#84) — new `.mantle/cost-policy.md` documents three named presets (`budget`, `balanced`, `quality`) with per-stage model defaults and one-line rationale. `.mantle/config.md` gains a validated `models:` block (active preset + per-stage `overrides`); precedence is overrides → preset → hardcoded `balanced` fallback. `core/project.py` exposes `StageModels` and `load_model_tier`; new `mantle model-tier` CLI wrapper emits the resolved stage→model JSON consumed by `build.md` Step 3. Every agent spawn in Steps 6–8 (implement, simplify, verify) now passes the per-stage model via the Agent `model:` parameter. Mechanical stages default to Sonnet/Haiku under `balanced`, cutting per-build cost without touching reasoning-heavy stages.
- **Structured acceptance criteria** (#77) — new CLI verbs `mantle flip-ac`, `mantle list-acs`, `mantle migrate-acs` promote ACs from free-text checklist items to first-class, addressable identifiers (`ac-01`, `ac-02`, …). `verify.md` and `review.md` prompts wire to `flip-ac` / `list-acs` so per-criterion pass/fail records feed `save-review-result` and `transition-issue-verified` without prose parsing. `migrate-acs` backfills legacy issues idempotently.
- **`.mantle/telemetry/` folder + baseline report skeleton** (#84) — introduced for build-run measurements. Ships with a method-doc + pricing-table skeleton (`baseline-<date>.md`) to be filled in by paired `/mantle:build` runs from a clean session; JSON companion file tracks the same data in machine-readable form for diff review.
- **`MANTLE_DIR` exported via `SessionStart` hook** (#82) — new Claude Code session hook resolves `mantle where` once and exports the result, so every prompt can substitute `$MANTLE_DIR/...` without re-resolving. `build.md` and other Claude Code prompts switched to the env-var form; a shell fallback handles sessions where the hook hasn't fired yet.
- **Configurable source/test paths for `collect-issue-diff-stats`** (#83) — `config.md` gains optional `diff_paths.source` / `diff_paths.tests` lists; the default is still `src/` + `tests/` so existing projects see no behaviour change. New `collect_issue_diff_stats_categorised` reports per-path-bucket stats; the legacy `collect_issue_diff_stats` wrapper keeps the `build.md` Step 7 grep contract intact. Fallback when `config.md` is missing is swallowed at the loader boundary.

### Changed
- **Verification-strategy precedence is config-first** (#81). `build.md` Step 8 and `verify.md` Step 3 now read `.mantle/config.md`'s `verification_strategy` field before falling back to `mantle introspect-project`. Previously the strategy could be silently regenerated on every run, overwriting the user's curated value.

### Fixed
- **cyclopts `--pass` / `--fail` binding on `flip-ac`** (#80) — flags now bind via `negative=` so `--pass` cleanly sets the AC state to pass and `--fail` to fail, rather than both aliasing the same parameter. Regression covered by tests that pin the cyclopts binding behaviour directly.

## [0.20.0] — 2026-04-18

### Added
- **Generic lifecycle hook seam** (#56) — mantle now invokes user-supplied `<mantle-dir>/hooks/on-<event>.sh` scripts on four issue lifecycle events: `issue-shaped` (after `save-shaped-issue`), `issue-implement-start` (after `transition-issue-implementing`), `issue-verify-done` (after `transition-issue-verified`), and `issue-review-approved` (after `transition-issue-approved`). Scripts receive positional args — issue number, new status, issue title — plus any env vars listed under `hooks_env:` in `.mantle/config.md` frontmatter. New `core/hooks.py` module hides the subprocess wiring; timeouts and non-zero exits log a warning and continue (fail-open — hooks never block the workflow). Missing scripts are a silent no-op. Mantle never imports a tracker library, never stores credentials, and never interprets the hook's env keys.
- **`mantle show-hook-example NAME`** — new CLI command under "Setup & plumbing" that prints a shipped reference hook script to stdout. Three examples ship as package data: `linear` (GraphQL via curl), `jira` (via Atlassian `acli`), and `slack` (incoming webhook). Each script has a setup-header comment block documenting install, authentication, and required `hooks_env:` entries. Typical use: `mantle show-hook-example linear > .mantle/hooks/on-issue-shaped.sh && chmod +x ...`.
- **`hooks_env:` config key** — new optional dict on `_ConfigFrontmatter` in `core/project.py`. Keys are opaque; mantle exports them as env vars to the hook process without interpretation. Absent or malformed `hooks_env:` degrades gracefully to an empty dict — the seam guarantees hook dispatch never blocks on a broken config.
- **`## Lifecycle hooks` section in README** — documents the hook authoring convention: path pattern, positional args, env passthrough, failure semantics, event list, and quickstart via `show-hook-example`.

## [0.19.0] — 2026-04-17

### Added
- **Baseline skills auto-loading** (#59) — new `core/baseline.py` resolves project-level skill requirements from `pyproject.toml`. Python 3.14+ projects now auto-get `python-314` in `skills_required` via `mantle update-skills` and compiled by `mantle compile`, so agents never misdiagnose valid PEP 758 syntax. Baseline resolution is a flat function, not a plugin registry — extend sibling helpers for future baselines (e.g. `pydantic-project-conventions` when Pydantic is detected).
- **Contextual CLI errors with recovery suggestions** (#51) — new `cli/errors` module exposes `exit_with_error(message, *, hint)` that renders a Rich-formatted red `Error:` line with an actionable yellow `Hint:` line on stderr and exits 1. All 16 existing CLI error paths migrated; `hint` is keyword-only so every call site is forced to be explicit. Generic `except Exception` handlers share the `UNEXPECTED_BUG_HINT` constant.
- **Telemetry session-id fallback** — `mantle build-start` / `build-finish` now fall back to reading `.mantle/.session-id` when `CLAUDE_SESSION_ID` is unset, enabling build telemetry outside of Claude Code's own session shell.
- **Test-tooling pilot** (#58) — `inline_snapshot` and `dirty-equals` adopted with scenario-fixture naming conventions documented in CLAUDE.md. Covers partial/unordered assertions and captured CLI/markdown output without hand-editing expected values.

### Changed
- **`plan-stories.md` Step 5c removed** (#60) — the redundant `mantle update-skills + compile` pair was already run by `implement.md` Step 3, so planning no longer duplicates the work or presents it as context-priming. `implement.md` is now the single owner of `update-skills + compile` for the implement path.
- **Build pipeline dirty-tree check tightened; simplifier scoped to the issue diff** — prevents false-positive review churn on unrelated uncommitted changes.
- **Module-import style and PEP 758 `except` syntax adopted** across `src/` and `tests/` — e.g. `from mantle.core import vault` + `vault.read_note(...)` instead of importing `read_note` directly. Aligns the codebase with CLAUDE.md's documented import rules.

### Fixed
- **`save-learning` accepts archived issues.** The documented retrospective flow runs `/mantle:review` (which archives) before `/mantle:retrospective` (which calls save-learning), but the issue-57 "strict" check rejected archived issues. Added `core.issues.find_issue_path_including_archive` that scans live first, then archive; `save_learning` now uses it, while other callers (`archive`, `stories`, `review`, `verify`) keep the live-only `find_issue_path` contract unchanged. Two pinning tests flipped from "fails clearly" to "succeeds"; four regression tests cover the new helper.
- **`resolve_mantle_dir` walks up to the primary worktree in local mode.** `mantle where` previously resolved to an empty `.mantle/` when invoked from a secondary git worktree, breaking `/mantle:build` from any worktree. Now parses `git worktree list --porcelain` and walks up to the primary repo's canonical `.mantle/`. Global-mode behaviour unchanged.

## [0.18.0] — 2026-04-15

### Added
- **Staleness regression test suite** (#50) — new `tests/test_staleness_regressions.py` pins post-archive behaviour across the side-effect-ordering family: `find_issue_path` returns None after `archive_issue`, `update_story_status` fails clearly when the parent issue has been archived, `save-review-result` refuses to write for unknown issues, and more. Acts as a shared safety net for follow-up fixes in the family.

### Fixed
- **`save-learning` silently writing after issue archival** (#57). `mantle save-learning --issue NN` used to write a learning file even when issue NN had been moved to `.mantle/archive/issues/`, producing an orphaned learning with no live issue to link back to. `core.learning.save_learning` now raises `IssueNotFoundError` via a `find_issue_path` precondition before any filesystem mutation; CLI catches it and exits 1 with an actionable message. Flips `test_save_learning_after_archive_fails_clearly` from `xfail` to a real pass.

## [0.17.1] — 2026-04-13

### Fixed
- `project.read_config` and `project.update_config` now resolve the config path via `resolve_mantle_dir` instead of hardcoding `project_root / .mantle/config.md`. Fixes `create_skill` (and any downstream `save-skill` flow) failing with `FileNotFoundError` in projects configured for global storage, which legitimately have no local `.mantle/` directory.

## [0.17.0] — 2026-04-12

### Added
- **Grouped `--help` output** (#48). `mantle --help` now renders commands in 8 labelled Cyclopts help panels (Setup & plumbing, Ideation, Design, Planning, Implementation, Verification, Knowledge, Reflection) in declared order. New `cli/groups.py` holds a central `GROUPS` registry; every `@app.command` is annotated with `group=GROUPS[key]`. Regression test covers panel ordering, per-command placement, the no-ungrouped-command invariant, and registry integrity.

## [0.16.0] — 2026-04-12

### Added
- **Build pipeline observability** (#54) — new `mantle build-start` and `mantle build-finish` CLI commands. `core/telemetry.py` parses Claude Code session JSONL (`~/.claude/projects/<slug>/<uuid>.jsonl`), groups sidechain clusters into per-story runs, and writes a structured markdown report to `.mantle/builds/build-<NN>-<timestamp>.md` with YAML frontmatter (model, tokens, duration, turn count) plus a rendered summary table. `implement.md` and `build.md` wired to call both around the implementation loop. Schema mirrors Anthropic issue #22625 for forward compatibility.
- **Issue-mode research** — `mantle save-research --issue N` skips the `idea.md` requirement, snapshots the issue title as `idea_ref`, and writes `.mantle/research/issue-<NN>-<focus>.md`. `/mantle:research` prompt documents both idea and issue modes. Lets the build pipeline dispatch research cleanly when an issue body lists prerequisite research questions.

### Changed
- **Build pipeline skill loading evidence requirement** — `build.md` gains Iron Law #5, two red-flag entries, and an explicit `Skills read:` report format listing the Read path for each loaded skill. Prose reinforcement alone ("as written") proved insufficient on issues 41 and 54; the new rule requires a `Read` tool call on each skill's `references/core.md` before "Skills loaded" can be reported.

## [0.15.0] — 2026-04-12

### Added
- **`/mantle:patterns` command** (#41) — surfaces recurring themes and per-slice confidence-delta trends across accumulated learnings. New `core/patterns.py` with `analyze_patterns` and `render_report`; thin CLI wrapper `mantle show-patterns`; new Claude Code prompt. Keyword-bucketed themes (testing, estimation, scope, tooling, shaping, worktree, ci, skills, other) — deterministic, no LLM calls.
- `core.issues.list_archived_issues` — sibling to `list_issues` for scanning `.mantle/archive/issues/`. Consumed by `analyze_patterns` so confidence-trend tables populate on mature projects where most issues are archived.

### Changed
- **Build pipeline skill loading** — `build.md` Step 4 now follows `shape-issue.md` Step 2.3 "Load skills" as written (active selection of 2-4 skills from `mantle list-skills`, read each), restoring issue 52's intended flow inside build mode. Previous override silently no-op'd when `mantle compile --issue NN` found no matches.
- **Build pipeline simplify verification** — `build.md` Step 7 now requires the orchestrator to re-run the project test command after the refactorer agent returns; the agent may lack bash access so its "tests passed" claim is unverified until confirmed.
- **`plan-stories.md`** — new rule: verify structural claims about sibling-module public APIs (attribute names, function signatures) before asserting them in story specs. Avoids implementer-confusion from unverified claims.

### Fixed
- `analyze_patterns` now joins against both live and archived issues; regex tolerates slug-less archive filenames (`issue-01.md`). Live issues win on collisions.

## [0.14.0] — 2026-04-12

### Added
- `mantle collect-issue-diff-stats` CLI command — reports `files`, `lines_added`, `lines_removed`, and `lines_changed` for an issue's commits as key=value lines, consumed by the build pipeline's simplify skip condition (#55).
- `DiffStats` NamedTuple and `collect_issue_diff_stats` in `core/simplify.py`, reusing the commit-grep pattern shared with `collect_issue_files` via new private helpers `_verify_issue_exists` and `_grep_issue_commits`.

### Changed
- **Single quality gate in the build pipeline** (#55). `/mantle:implement` no longer spawns a per-story code-reviewer agent after each story — TDD covers spec compliance and the post-implementation simplify step becomes the sole code-quality gate with cross-story context.
- Build pipeline simplify skip condition now uses a composite heuristic: skip only when `files ≤ 3` AND `lines_changed ≤ 50` (previously file count alone).

## [0.13.0] — 2026-04-12

### Added
- **Skill injection into shaping** (#52). `/mantle:shape-issue` now agent-curates relevant vault skills and injects their knowledge into the shaping prompt. New `SkillSummary` model and enriched `list-skills` CLI output surface slug + description pairs for agent selection.
- **Standardised skill anatomy** (#53). Vault skills now follow a what/why/when/how template with Common Rationalizations, Red Flags, and Verification sections — executable workflows with anti-rationalization guardrails, not passive reference prose.
- **Marker-based progressive disclosure** (#53). New `<!-- mantle:reference -->` marker in vault skill source splits compiled output: main workflow inline in `SKILL.md`, deep reference material in `references/core.md`. Un-markered skills fall back to the existing line-count heuristic — fully backwards compatible.

### Changed
- 5 high-use vault skills migrated to the new anatomy as proof of concept: `design-review`, `software-design-principles`, `python-project-conventions`, `cli-design-best-practices`, `cyclopts`.
- `/mantle:add-skill` prompt now generates skills in the new anatomy.

## [0.12.2] — 2026-04-10

### Fixed
- Remove non-existent `--global` flag from `mantle install` example in README.

## [0.12.1] — 2026-04-10

### Changed
- **Taxonomy-aware tag guidance** (#49). Rewrote add-skill Step 6 to check existing tags first, prefer coarse-grained names, and include good/bad examples. Migrated existing vault tags — 49 down to 41 with meaningful clusters (`topic/scraping` shared by 3 skills, `domain/finance` by 8).

### Fixed
- `generate_index_notes` now auto-removes orphaned generated index files for tags that no longer exist on any skill. Manual index files are preserved.

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

[0.23.0]: https://github.com/chonalchendo/mantle/releases/tag/v0.23.0
[0.22.0]: https://github.com/chonalchendo/mantle/releases/tag/v0.22.0
[0.21.0]: https://github.com/chonalchendo/mantle/releases/tag/v0.21.0
[0.20.0]: https://github.com/chonalchendo/mantle/releases/tag/v0.20.0
[0.19.0]: https://github.com/chonalchendo/mantle/releases/tag/v0.19.0
[0.18.0]: https://github.com/chonalchendo/mantle/releases/tag/v0.18.0
[0.17.1]: https://github.com/chonalchendo/mantle/releases/tag/v0.17.1
[0.17.0]: https://github.com/chonalchendo/mantle/releases/tag/v0.17.0
[0.16.0]: https://github.com/chonalchendo/mantle/releases/tag/v0.16.0
[0.15.0]: https://github.com/chonalchendo/mantle/releases/tag/v0.15.0
[0.14.0]: https://github.com/chonalchendo/mantle/releases/tag/v0.14.0
[0.13.0]: https://github.com/chonalchendo/mantle/releases/tag/v0.13.0
[0.12.2]: https://github.com/chonalchendo/mantle/releases/tag/v0.12.2
[0.12.1]: https://github.com/chonalchendo/mantle/releases/tag/v0.12.1
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
